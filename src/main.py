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
    get_all_offers,
)
from migrations import (
    download_all_offers,
    download_all_landings,
    upload_all_offers,
    upload_all_landings,
)

from process_offer import process_offer, process_all_offers
from phone_inputs import PHONE_RULES, PHONE_ASSETS
from email_validator import EMAIL_RULES, EMAIL_ASSETS
from macros import MACROS_RULES
from rules_engine import apply_rules
from audit import audit_all_offers
from fix_macros_duples import fix_back_duplicates

import httpx
import zipfile
import io
import base64
from pathlib import Path
import re

print("Keitaro URL:", KEITARO_URL)
print("API key exists:", bool(KEITARO_API_KEY))
print("URL exists:", bool(KEITARO_URL))
ALL_RULES = EMAIL_RULES + PHONE_RULES + MACROS_RULES
ALL_ASSETS = {**EMAIL_ASSETS, **PHONE_ASSETS}


# upload_landing_pages("landings_archives")
# upload_offer_pages("offers_archives")

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

""" разработка функционала по работе RULES """
# pattern_with_label = re.compile(
#     r'<label\b[^>]*>(?:(?!<input\b).)*<input\b[^>]*\bname=["\']phone["\'][^>]*/?>(?:(?!</label>).)*?</label>',
#     re.IGNORECASE | re.DOTALL
# )
# pattern_without_label = re.compile(r'<input\b[^>]*\bname=["\']phone["\'][^>]*/?>', re.IGNORECASE)

# NEW_PHONE_HTML = '''<div class="intgrtn-input-holder intgrtn-input-holder-phone">
#         <div class="phone-wrapper">
#           <label>Teléfono</label>
#             <input class="intgrtn-input phonelist phone-valid" id="phone" type="tel" name="phone" placeholder="Número de teléfono" required autocomplete="off">
#             <input name="full_phone" class="full_phone" type="hidden" value="">
#             <div class="error-message" id="error-phone-es">Por favor ingresa un número de teléfono válido</div>
#         </div>
#     </div>'''

# old_pattern = re.compile(r'name=["\']phone["\'][^>]*type=["\']tel', re.IGNORECASE)
# test_dir = Path(__file__).parent / "test_forms"
# for f in sorted(test_dir.glob("form*.html")):
#     content = f.read_text(encoding="utf-8")
#     new_content, status = replace_phone_input(content, NEW_PHONE_HTML)
#     old_left = bool(old_pattern.search(new_content))
#     print(f"{f.name}: {status}")
#     print(f"  NEW block count: {new_content.count('intgrtn-input-holder-phone')}")
#     print(f"  OLD input left: {old_left}")

# test_dir = Path(__file__).parent / "test_forms"
# for f in sorted(test_dir.glob("form*.html")):
#     content = f.read_text(encoding="utf-8")
#     new_content, log = apply_rules(content, PHONE_RULES)
#     new_content2, log2 = apply_rules(new_content, PHONE_RULES)
#     print(f"\n{f.name}:")
#     for entry in log:
#         print(f"  {entry['rule_id']}: {entry['status']}")
#     print(f"  NEW phone block: {new_content.count('intgrtn-input-holder-phone')}")
#     print(f"\n{f.name}:")
#     for entry in log2:
#         print(f"  {entry['rule_id']}: {entry['status']}")
#     print(f"  NEW phone block: {new_content2.count('intgrtn-input-holder-phone')}")
# test_ids = [47]
# for oid in test_ids:
#     status, log = process_offer(oid, ALL_RULES, ALL_ASSETS, dry_run=True)
#     print(f"Status: {status}")
#     for entry in log:
#         file_ = entry.get("file") or "—"
#         rule_ = entry.get("rule_id") or "—"
#         print(f"  [{file_}] {rule_}: {entry['status']}")


process_all_offers(ALL_RULES, ALL_ASSETS, dry_run=False, offers=False)

""" функционал работы с макросами """
# test_dir = Path(__file__).parent / "test_forms"
# form7_path = test_dir / "form7.html"
# form7 = form7_path.read_text(encoding="utf-8")
# new_content, log = apply_rules(form7, MACROS_RULES)
# print(new_content)
# new_content2, log2 = apply_rules(new_content, MACROS_RULES)
# print("=== SECOND RUN ===")
# for entry in log2:
#     print(f"  {entry['rule_id']}: {entry['status']}")
# print(f"\nUnchanged: {new_content == new_content2}")
# status, log = process_offer(40, ALL_RULES, ALL_ASSETS, dry_run=False)
# print(f"Status: {status}")
# for entry in log:
#     file_ = entry.get("file") or "—"
#     rule_ = entry.get("rule_id") or "—"
#     print(f"  [{file_}] {rule_}: {entry['status']}")

""" audit offers to errors """
# problems = audit_all_offers()
# Список из аудита
# PROBLEM_IDS = [122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 64, 63, 62, 61, 60, 59, 58, 57, 51, 50, 47, 46, 45, 44, 14, 12, 8]   # ← вставь полностью

# fixed, skipped, failed = fix_back_duplicates(PROBLEM_IDS)
