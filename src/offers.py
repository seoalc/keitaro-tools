import base64
import httpx
from pathlib import Path
import clamd

from config import KEITARO_URL, KEITARO_API_KEY

def get_all_directory_files(directory):
    return [path for path in Path(directory).iterdir() if path.is_file() and path.suffix.lower() == ".zip"]

def get_offer_name(path):
    return path.stem

def get_geo(path):
    return path.stem[:2]

def get_groups():
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/groups?type=offers",
        headers={"Api-Key": KEITARO_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def get_group_id(geo):
    groups = get_groups()
    for group in groups:
        if group["name"][:2].lower() == geo.lower():
            return group["id"]
    return None

def upload_offer_pages(directory):
    directory_files = get_all_directory_files(directory)
    for path in directory_files:
        scan_result = scan_file(path)
        print("Scan result for", path.name, ":", scan_result)
        if scan_result != "OK":
            print("Skipping upload for", path.name, "due to scan result:", scan_result)
            continue
        geo = get_geo(path)
        group_id = get_group_id(geo)
        offer_name = get_offer_name(path)

        result = upload_offer_page(
            path,
            offer_name,
            group_id,
        )

        print("Uploaded:", path.name, "→ Offer #", result["id"])

def upload_offer_page(archive_path, offer_name, group_id):
    
    with open(archive_path, "rb") as file:
        archive = file.read()
        archive_b64 = base64.b64encode(archive).decode("utf-8")

    payload = {
        "name": offer_name,
        "group_id": group_id,
        "offer_type": "local",
        "affiliate_network_id": 1,
        "payout_value": 0,
        "payout_currency": "USD",
        "payout_type": "CPA",
        "payout_auto": True,
        "payout_upsell": True,
        "archive": archive_b64,
    }

    response = httpx.post(
        f"{KEITARO_URL}/admin_api/v1/offers",
        headers={"Api-Key": KEITARO_API_KEY},
        json=payload,
    )

    response.raise_for_status()
    return response.json()

def scan_file(path):
    client = clamd.ClamdNetworkSocket(host="clamav", port=3310)

    with open(path, "rb") as file:
        result = client.instream(file)["stream"][0]

    return result