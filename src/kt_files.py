import httpx

from config import KEITARO_URL, KEITARO_API_KEY

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

####### Загрузка архивов #######

def download_offer_archive(offer_id):
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/offers/{offer_id}/download",
        headers={"Api-Key": KEITARO_API_KEY},
    )

    response.raise_for_status()

    return response.content