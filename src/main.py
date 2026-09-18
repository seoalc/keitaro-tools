from config import KEITARO_URL, KEITARO_API_KEY
from landings import upload_landing_pages, scan_file
from offers import upload_offer_pages, upload_offer_page
from kt_files import (
    update_offer_file,
    get_offer_file,
    get_offer_files_structure,
    walk_files,
    inject_validator_into_offer,
    download_offer_archive,
    modify_offer_archive,
    inject_validator_into_all_offers,
)
from migrations import (
    download_all_offers,
    download_all_landings,
    upload_all_offers,
    upload_all_landings,
)
import httpx
import zipfile
import io
import base64
from pathlib import Path

print("Keitaro URL:", KEITARO_URL)
print("API key exists:", bool(KEITARO_API_KEY))
print("URL exists:", bool(KEITARO_URL))


upload_landing_pages("landings_archives")
upload_offer_pages("offers_archives")

# original = get_offer_file(40, "send.php")
# update_offer_file(40, "send.php", original)
# after = get_offer_file(40, "send.php")
# print("MATCH:", original == after)


""" операции с миграциями офферов """
# download_all_offers(out_dir="offers_archives_old", mapping_path="offers_archives_old/mapping_offers.json")
# upload_all_offers("offers_archives_old/mapping_offers.json", "offers_archives_old")
# update_mapping_with_funnel("offers_archives_old/mapping_offers.json")

""" операции с миграциями лендингов """
# download_all_landings(out_dir="landing_archives_old", mapping_path="landing_archives_old/mapping_landings.json")
# upload_all_landings("landing_archives_old/mapping_landings.json", archive_dir="landing_archives_old")


# update_offer_file(40, "files/test2.txt", "hello2")

""" внедрение валидатора поля email в офферы с проверкой """
# js_path = Path(__file__).parent / "email-validation.js"
# with open(js_path, "r", encoding="utf-8") as f:
#     js = f.read()
# log_path = Path(__file__).parent / "inject_log.txt"
# inject_validator_into_all_offers(js, log_path=log_path)

""" запуск внедрения валидатора поля email на конкретных офферах по id """
# test_ids = [324, 323, 195, 194]
# for oid in test_ids:
#     try:
#         data = download_offer_archive(oid)
#         print(f"[{oid}] downloaded, {len(data)} bytes")
#         modified = modify_offer_archive(data, js)
#         print(f"[{oid}] modified, {len(modified)} bytes")
#         archive_b64 = base64.b64encode(modified).decode("utf-8")
#         response = httpx.put(
#             f"{KEITARO_URL}/admin_api/v1/offers/{oid}",
#             headers={"Api-Key": KEITARO_API_KEY},
#             json={"archive": archive_b64},
#             timeout=300.0,
#         )
#         response.raise_for_status()
#         print(f"[{oid}] OK")
#     except Exception as e:
#         import traceback
#         print(f"[{oid}] FAILED: {type(e).__name__}: {e}")
#         traceback.print_exc()
