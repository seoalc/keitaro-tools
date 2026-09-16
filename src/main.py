from config import KEITARO_URL, KEITARO_API_KEY
from landings import upload_landing_pages, scan_file
from offers import upload_offer_pages, upload_offer_page
from kt_files import update_offer_file, get_offer_file, download_offer_archive
import httpx

print("Keitaro URL:", KEITARO_URL)
print("API key exists:", bool(KEITARO_API_KEY))
print("URL exists:", bool(KEITARO_URL))


# upload_landing_pages("landings_archives")
# upload_offer_pages("offers_archives")
# original = get_offer_file(40, "send.php")
# update_offer_file(40, "send.php", original)
# after = get_offer_file(40, "send.php")
# print("MATCH:", original == after)

data = download_offer_archive(40)
print("Bytes:", len(data))
print("Magic:", data[:4])
with open("offers_archives/40_offer_archive_sa.zip", "wb") as f:
    f.write(data)