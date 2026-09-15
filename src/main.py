from config import KEITARO_URL, KEITARO_API_KEY
from landings import upload_landing_page, get_groups, upload_landing_pages, scan_file

print("Keitaro URL:", KEITARO_URL)
print("API key exists:", bool(KEITARO_API_KEY))
print("URL exists:", bool(KEITARO_URL))


upload_landing_pages("landings_archives")