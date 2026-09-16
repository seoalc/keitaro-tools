from config import KEITARO_URL, KEITARO_API_KEY
from landings import upload_landing_pages, scan_file
from offers import upload_offer_pages, upload_offer_page
import httpx

print("Keitaro URL:", KEITARO_URL)
print("API key exists:", bool(KEITARO_API_KEY))
print("URL exists:", bool(KEITARO_URL))


upload_landing_pages("landings_archives")
upload_offer_pages("offers_archives")
# response = httpx.get(
#     f"{KEITARO_URL}/admin_api/v1/offers/40",
#     headers={"Api-Key": KEITARO_API_KEY},
# )

# response.raise_for_status()

# print(response.json())