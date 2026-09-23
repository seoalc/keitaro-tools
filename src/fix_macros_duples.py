import io
import base64
import zipfile
import httpx
from pathlib import Path
from config import KEITARO_URL, KEITARO_API_KEY
from process_offer import download_offer_archive

OLD_BLOCK = '<script>\nwindow.back = "{offer}";\n</script>\n{_back}'
NEW_BLOCK = '<script>\nwindow.back = "{offer}";\n</script>'


def remove_duplicate_back_from_archive(data):
    """
    Если в html/php файлах есть наш блок с {_back} и {_back} встречается >1 раз —
    убираем {_back} из нашего блока.
    Возвращает (new_data, changed).
    """
    src = zipfile.ZipFile(io.BytesIO(data), "r")
    out_buffer = io.BytesIO()
    changed = False
    
    with zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            name = item.filename
            if item.is_dir():
                continue
            
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in ("html", "htm", "php"):
                content = src.read(name).decode("utf-8", errors="replace")
                
                if content.count("{_back}") > 1 and OLD_BLOCK in content:
                    new_content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)
                    if new_content != content:
                        content = new_content
                        changed = True
                
                dst.writestr(name, content.encode("utf-8"))
            else:
                dst.writestr(name, src.read(name))
    
    src.close()
    
    if not changed:
        return data, False
    
    return out_buffer.getvalue(), True


def fix_back_duplicates(offer_ids):
    fixed = []
    failed = []
    skipped = []
    
    for oid in offer_ids:
        try:
            data = download_offer_archive(oid)
            new_data, changed = remove_duplicate_back_from_archive(data)
            
            if not changed:
                skipped.append(oid)
                print(f"[{oid}] no change")
                continue
            
            archive_b64 = base64.b64encode(new_data).decode("utf-8")
            response = httpx.put(
                f"{KEITARO_URL}/admin_api/v1/offers/{oid}",
                headers={"Api-Key": KEITARO_API_KEY},
                json={"archive": archive_b64},
                timeout=300.0,
            )
            response.raise_for_status()
            fixed.append(oid)
            print(f"[{oid}] FIXED")
        except Exception as e:
            failed.append((oid, str(e)))
            print(f"[{oid}] FAILED: {e}")
    
    print(f"\nFixed: {len(fixed)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Failed: {len(failed)}")
    return fixed, skipped, failed


# Список из аудита
# PROBLEM_IDS = [633, 632, 631, 630, 586, 585, 47]   # ← вставь полностью

# fixed, skipped, failed = fix_back_duplicates(PROBLEM_IDS)