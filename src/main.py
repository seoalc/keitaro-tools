from config import KEITARO_URL, KEITARO_API_KEY
from landings import upload_landing_pages, scan_file
from offers import upload_offer_pages, upload_offer_page
from kt_files import update_offer_file, get_offer_file, download_offer_archive
from migrations import download_all_offers, download_all_landings, upload_all_offers, upload_all_landings
import httpx

print("Keitaro URL:", KEITARO_URL)
print("API key exists:", bool(KEITARO_API_KEY))
print("URL exists:", bool(KEITARO_URL))


upload_landing_pages("landings_archives")
upload_offer_pages("offers_archives")
# original = get_offer_file(40, "send.php")
# update_offer_file(40, "send.php", original)
# after = get_offer_file(40, "send.php")
# print("MATCH:", original == after)

"""миграция офферов"""
# download_all_offers(out_dir="offers_archives_old", mapping_path="offers_archives_old/mapping_offers.json")
# upload_all_offers("offers_archives_old/mapping_offers.json", "offers_archives_old")
# update_mapping_with_funnel("offers_archives_old/mapping_offers.json")
"""миграция лендингов"""
# download_all_landings(out_dir="landing_archives_old", mapping_path="landing_archives_old/mapping_landings.json")
# upload_all_landings("landing_archives_old/mapping_landings.json", archive_dir="landing_archives_old")