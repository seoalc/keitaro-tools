import os
import httpx


keitaro_url = os.getenv("KEITARO_URL")
keitaro_api_key = os.getenv("KEITARO_API_KEY")

print("Keitaro URL:", keitaro_url)
print("API key exists:", bool(keitaro_api_key))
print("URL exists:", bool(keitaro_url))

response = httpx.get(f"{keitaro_url}/admin_api/v1/landing_pages", headers={"Api-Key": keitaro_api_key})
print("Response status code:", response.status_code)
response.raise_for_status()
data = response.json()

print(type(data))
print(len(data))