import io
import zipfile
import base64
import httpx
from pathlib import Path
import time

from config import KEITARO_URL, KEITARO_API_KEY
from rules_engine import apply_rules
from kt_files import download_offer_archive

TEXT_EXTS = ("html", "htm", "php")

def get_all_offers():
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/offers",
        headers={"Api-Key": KEITARO_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def is_text_file(name):
    if "." not in name:
        return False
    ext = name.rsplit(".", 1)[-1].lower()
    return ext in TEXT_EXTS

def modify_archive(data, rules, assets):
    log = []
    track_changes = False
    assets_seen = set()   # какие assets мы уже встретили в архиве
    
    src = zipfile.ZipFile(io.BytesIO(data), "r")
    out_buffer = io.BytesIO()
    
    with zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            name = item.filename
            
            # Пропускаем директории
            if item.is_dir():
                continue
            
            # 1. Это asset? — заменяем содержимое
            if name in assets:
                old_content = src.read(name)
                new_content = assets[name]
                if isinstance(new_content, str):
                    new_content = new_content.encode("utf-8")
                
                if old_content != new_content:
                    dst.writestr(name, new_content)
                    track_changes = True
                    log.append({"file": name, "rule_id": None, "status": "asset_replaced"})
                else:
                    dst.writestr(name, old_content)
                    log.append({"file": name, "rule_id": None, "status": "asset_unchanged"})
                
                assets_seen.add(name)
                continue
            
            # 2. Это html/php? — применяем правила
            if is_text_file(name):
                content = src.read(name).decode("utf-8", errors="replace")
                new_content, rules_log = apply_rules(content, rules)
                
                # Логируем статусы правил для этого файла
                for entry in rules_log:
                    log.append({
                        "file": name,
                        "rule_id": entry["rule_id"],
                        "status": entry["status"],
                    })
                
                if new_content != content:
                    track_changes = True
                
                dst.writestr(name, new_content.encode("utf-8"))
                continue
            
            # 3. Всё остальное — копируем как есть
            dst.writestr(name, src.read(name))
        
        # 4. Добавляем assets, которых не было в архиве
        for path, content in assets.items():
            if path in assets_seen:
                continue
            dst.writestr(path, content)
            track_changes = True
            log.append({"file": path, "rule_id": None, "status": "asset_added"})
    
    src.close()
    
    # Если ничего не изменилось — вернуть оригинал
    if not track_changes:
        return data, log
    
    return out_buffer.getvalue(), log


def process_offer(offer_id, rules, assets, dry_run=True):
    try:
        data = download_offer_archive(offer_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            # Нет локальных файлов (redirect, external, preloaded)
            return "skipped", [{"file": None, "rule_id": None, "status": "no files (redirect?)"}]
        raise   # остальные ошибки — наверх
    new_data, modify_log = modify_archive(data, rules, assets)
    
    # Агрегируем статусы по правилам (пропускаем записи без rule_id)
    rule_status = {}
    for entry in modify_log:
        rule_id = entry.get("rule_id")
        if rule_id is None:
            continue
        status = entry["status"]
        current = rule_status.get(rule_id)
        if current == "applied":
            continue
        if status == "applied":
            rule_status[rule_id] = "applied"
        elif status == "skipped" and current != "applied":
            rule_status[rule_id] = "skipped"
        elif current is None:
            rule_status[rule_id] = status
    
    # Проверяем required-правила
    failed_required = []
    for rule in rules:
        if rule.get("required") and rule_status.get(rule["id"]) == "not_found":
            failed_required.append(rule["id"])
    
    if failed_required:
        modify_log.append({
            "file": None, "rule_id": None,
            "status": f"required rules not found: {failed_required}",
        })
        return "skipped", modify_log
    
    if new_data == data:
        modify_log.append({"file": None, "rule_id": None, "status": "no changes"})
        return "skipped", modify_log
    
    if dry_run:
        return "dry_run", modify_log
    
    archive_b64 = base64.b64encode(new_data).decode("utf-8")
    response = httpx.put(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}",
        headers={"Api-Key": KEITARO_API_KEY},
        json={"archive": archive_b64},
        timeout=300.0,
    )
    response.raise_for_status()
    return "ok", modify_log

def process_all_offers(rules, assets, dry_run=True, offers=False):
    if offers:
        offers = offers
    else:
        offers = get_all_offers()   # новый Keitaro
    offers = [o for o in offers if o.get("offer_type") == "local"]
    results = {"ok": [], "skipped": [], "dry_run": [], "failed": []}
    
    log_path = Path(__file__).parent / "process_log.txt"
    with open(log_path, "a", encoding="utf-8") as log:
        for offer in offers:
            offer_id = offer["id"]
            try:
                status, entries = with_retry(
                    process_offer, offer_id, rules, assets,
                    attempts=3, delay=5, dry_run=dry_run,
                )
                results[status].append(offer_id)
                log.write(f"[{offer_id}] {status}\n")
                log.flush()
                print(f"[{offer_id}] {status}")
                log.write(format_log_summary(offer_id, status, entries) + "\n")
            except Exception as e:
                results["failed"].append((offer_id, str(e)))
                log.write(f"[{offer_id}] FAILED: {e}\n")
                log.flush()
                print(f"[{offer_id}] FAILED: {e}")
    
    print(f"\nOK: {len(results['ok'])}")
    print(f"Skipped: {len(results['skipped'])}")
    print(f"Dry-run: {len(results['dry_run'])}")
    print(f"Failed: {len(results['failed'])}")
    if results["failed"]:
        print("Failed ids:", [x[0] for x in results["failed"]])
    return results

"""
    Вызывает fn(*args, **kwargs). При сетевых ошибках — до attempts попыток с паузой.
    Возвращает результат fn или бросает последнее исключение.
"""
def with_retry(fn, *args, attempts=3, delay=5, **kwargs):
    last_exc = None
    for attempt in range(attempts):
        try:
            return fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                # 4xx (кроме 429) — не ретраим
                raise
            last_exc = e
            if attempt < attempts - 1:
                print(f"  retry {attempt + 1}/{attempts - 1}: {e}")
                time.sleep(delay)
        except httpx.TimeoutException as e:
            last_exc = e
            if attempt < attempts - 1:
                print(f"  retry {attempt + 1}/{attempts - 1}: {e}")
                time.sleep(delay)
    raise last_exc

def format_log_summary(offer_id, status, entries):
    rule_status = {}
    asset_status = {}
    
    for e in entries:
        if e.get("rule_id"):
            rule_id = e["rule_id"]
            st = e["status"]
            current = rule_status.get(rule_id)
            # приоритет: applied > skipped > not_found > прочее
            if current == "applied":
                continue
            if st == "applied":
                rule_status[rule_id] = "applied"
            elif st == "skipped" and current != "applied":
                rule_status[rule_id] = "skipped"
            elif current is None:
                rule_status[rule_id] = st
        elif e.get("file"):
            asset_status[e["file"]] = e["status"]
    
    rules_str = ", ".join(f"{k}={v}" for k, v in rule_status.items())
    assets_str = ", ".join(f"{k}={v}" for k, v in asset_status.items())
    
    return f"[{offer_id}] {status} | rules: {rules_str} | assets: {assets_str}"