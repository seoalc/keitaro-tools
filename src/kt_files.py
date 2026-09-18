import httpx
import zipfile
import io
import base64
import time

from config import KEITARO_URL, KEITARO_API_KEY

SCRIPT_TAG = '<script src="files/email-validation.js"></script>'
JS_PATH = "files/email-validation.js"

def get_all_offers():
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/offers",
        headers={"Api-Key": KEITARO_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def get_offer_file(offer_id, file_path):
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}/get_file",
        headers={"Api-Key": KEITARO_API_KEY},
        params={
            "path": file_path
        }
    )

    response.raise_for_status()

    return response.json()["data"]

def get_offer_files_structure(offer_id):
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}/get_structure",
        headers={"Api-Key": KEITARO_API_KEY}
    )
    response.raise_for_status()
    return response.json()

def walk_files(node, out=None):
    """
    Рекурсивно обходит дерево файлов Keitaro.
    node — может быть список (корень) или один узел (dict).
    Возвращает плоский список файлов (dict'ов), без папок.
    """
    if out is None:
        out = []

    # Если пришёл список — обходим каждый элемент
    if isinstance(node, list):
        for item in node:
            walk_files(item, out)
        return out

    # Если это файл — добавляем
    if node.get("type") == "file":
        out.append(node)

    # Если есть дети — рекурсивно обходим
    for child in node.get("children") or []:
        walk_files(child, out)

    return out


def get_html_php_files(structure):
    """Возвращает только файлы с расширением php/html/htm."""
    files = walk_files(structure)
    return [f for f in files if f.get("ext") in ("php", "html", "htm")]

def update_offer_file(offer_id, file_path, content):
    response = httpx.put(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}/update_file",
        headers={"Api-Key": KEITARO_API_KEY},
        params={
            "path": file_path,
            "data": content
        }
    )
    response.raise_for_status()
    return response.json()

def inject_validator_into_offer(offer_id, js_content, dry_run=True):
    log = []
    
    # 1. Заливаем JS
    log.append(f"[{offer_id}] upload files/email-validation.js")
    if not dry_run:
        update_offer_file(offer_id, "files/email-validation.js", js_content)
    
    # 2. Получаем структуру и список html/php
    structure = get_offer_files_structure(offer_id)
    files = get_html_php_files(structure)
    
    # 3. По каждому файлу
    for f in files:
        path = f["path"]
        content = get_offer_file(offer_id, path)
        
        if "email-validation.js" in content:
            log.append(f"[{offer_id}] {path} — already injected")
            continue
        
        # вставка
        if "</body>" in content:
            new_content = content.replace("</body>", SCRIPT_TAG + "\n</body>", 1)
        else:
            new_content = content + "\n" + SCRIPT_TAG
        
        log.append(f"[{offer_id}] {path} — injected")
        if not dry_run:
            update_offer_file(offer_id, path, new_content)
    
    return log

def add_offer_file(offer_id, file_path, content):
    response = httpx.post(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}/add_file",
        headers={"Api-Key": KEITARO_API_KEY},
        params={"path": file_path},
        json={"data": content},
    )
    response.raise_for_status()
    return response.json()

####### Загрузка архивов #######

def download_offer_archive(offer_id):
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}/download",
        headers={"Api-Key": KEITARO_API_KEY},
    )

    response.raise_for_status()

    return response.content

def modify_offer_archive(data: bytes, js_content: str) -> bytes:
    """
    Принимает байты zip-архива оффера, возвращает новые байты:
    - добавляет/обновляет files/email-validation.js
    - вставляет SCRIPT_TAG в html/php файлы (если ещё нет)
    """
    src = zipfile.ZipFile(io.BytesIO(data), "r")
    out_buffer = io.BytesIO()

    with zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as dst:
        js_written = False

        for item in src.infolist():
            name = item.filename

            # Пропускаем директории (записи вроде "./", "files/./")
            if item.is_dir():
                continue

            # JS-файл — заменяем на новый контент
            if name == JS_PATH:
                dst.writestr(name, js_content)
                js_written = True
                continue

            # HTML/PHP — читаем, модифицируем, пишем
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in ("html", "htm", "php"):
                content = src.read(name).decode("utf-8", errors="replace")
                
                # Вставляем только в реальные HTML-страницы
                if "<body" not in content.lower():
                    dst.writestr(name, content.encode("utf-8"))
                    continue

                if "email-validation.js" not in content:
                    if "</body>" in content:
                        content = content.replace(
                            "</body>", f"{SCRIPT_TAG}\n</body>", 1
                        )
                    else:
                        content = content + "\n" + SCRIPT_TAG

                dst.writestr(name, content.encode("utf-8"))
                continue

            # Всё остальное — копируем как есть (шрифты, картинки, send.php...)
            dst.writestr(name, src.read(name))

        # Если JS-файла в архиве не было — добавляем
        if not js_written:
            dst.writestr(JS_PATH, js_content)

    src.close()
    return out_buffer.getvalue()

def process_offer(offer_id, js_content):
    data = download_offer_archive(offer_id)
    modified = modify_offer_archive(data, js_content)
    if modified == data:
        return "skipped"
    archive_b64 = base64.b64encode(modified).decode("utf-8")
    response = httpx.put(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}",
        headers={"Api-Key": KEITARO_API_KEY},
        json={"archive": archive_b64},
        timeout=300.0,
    )
    response.raise_for_status()
    return "ok"

def inject_validator_into_all_offers(js_content, log_path="inject_log.txt"):
    offers = get_all_offers()
    results = {"ok": [], "failed": [], "skipped": []}
    
    with open(log_path, "a", encoding="utf-8") as log:
        for offer in offers:
            offer_id = offer["id"]
            try:
                status = with_retry(process_offer, offer_id, js_content, attempts=3, delay=5)
                results[status].append(offer_id)
                log.write(f"[{offer_id}] {status}\n")
                print(f"[{offer_id}] {status}")
            except Exception as e:
                results["failed"].append((offer_id, str(e)))
                log.write(f"[{offer_id}] FAILED: {e}\n")
                print(f"[{offer_id}] FAILED: {e}")
    
    print(f"\nOK: {len(results['ok'])}")
    print(f"Skipped: {len(results['skipped'])}")
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
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            last_exc = e
            if attempt < attempts - 1:
                print(f"  retry {attempt + 1}/{attempts - 1}: {e}")
                time.sleep(delay)
    raise last_exc