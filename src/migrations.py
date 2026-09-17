import httpx
import re
import json
from pathlib import Path
import time
import base64

from config import KEITARO_URL, KEITARO_API_KEY, KEITARO_OLD_URL, KEITARO_OLD_API_KEY, KEITARO_ASIA_URL, KEITARO_ASIA_API_KEY

######### Работа со старыми Keitaro #########
######### Загрузка офферов #########

def get_all_offers_old():
    response = httpx.get(
        f"{KEITARO_ASIA_URL}/admin_api/v1/offers",
        headers={"Api-Key": KEITARO_ASIA_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def get_groups_old():
    response = httpx.get(
        f"{KEITARO_ASIA_URL}/admin_api/v1/groups?type=offers",
        headers={"Api-Key": KEITARO_ASIA_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def get_group_map_old():
    groups = get_groups_old()
    group_map = {}
    for group in groups:
        group_map[group["id"]] = group["name"]
    return group_map

def sanitize_filename(filename):
    sanitized = re.sub(r'[| }{#)(/\'*"&%\\:?><+=;,~$@]', '_', filename)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized

def download_offer_archive(offer_id):
    for attempt in range(3):
        try:
            response = httpx.get(
                f"{KEITARO_ASIA_URL}/admin_api/v1/offers/{offer_id}/download",
                headers={"Api-Key": KEITARO_ASIA_API_KEY},
                timeout=120.0,
            )
            response.raise_for_status()
            return response.content
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == 2:
                raise
            print(f"  retry {attempt+1} for offer {offer_id}: {e}")
            time.sleep(5)

def extract_value(values, key="funnel"):
    """Достаёт значение кастомного поля по имени. Возвращает None, если нет."""
    for v in values or []:
        if v.get("name") == key:
            return v.get("value")
    return None

# обновление маппинга, добавление values
def update_mapping_with_funnel(
    mapping_path="offers_archives_old/mapping_offers.json",
):
    # 1. Читаем текущий маппинг
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # 2. Забираем офферы со старого Keitaro
    offers = get_all_offers_old()
    offers_by_id = {str(o["id"]): o for o in offers}

    # 3. Обходим маппинг и дописываем funnel
    updated = 0
    missing = []
    for offer_id, info in mapping.items():
        offer = offers_by_id.get(offer_id)
        if offer is None:
            missing.append(offer_id)
            continue
        funnel = extract_value(offer.get("values"), "funnel")
        info["funnel"] = funnel
        updated += 1

    # 4. Сохраняем обратно (перезапись)
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"Updated {updated} entries with funnel.")
    if missing:
        print(f"Offers in mapping but not found in old Keitaro: {missing}")
    # сколько вообще с непустым funnel
    with_funnel = sum(1 for i in mapping.values() if i.get("funnel"))
    print(f"Entries with non-empty funnel: {with_funnel} / {len(mapping)}")

def download_all_offers(out_dir="offers_archives_old", mapping_path="offers_archives_old/mapping_offers.json"):
    Path(out_dir).mkdir(exist_ok=True)
    
    offers = get_all_offers_old()
    group_map = get_group_map_old()
    mapping = {}
    failed = []
    
    for offer in offers:
        offer_id = offer["id"]
        name = offer["name"]
        geo = group_map.get(offer["group_id"])
        filename = sanitize_filename(name) + "_sa.zip"
        
        try:
            data = download_offer_archive(offer_id)
            with open(Path(out_dir) / filename, "wb") as f:
                f.write(data)

            funnel = extract_value(offer.get("values"), "funnel")
            mapping[str(offer_id)] = {
                "id": offer_id,
                "filename": filename,
                "name": name,
                "geo": geo,
                "funnel": funnel,
            }
            # mapping[str(offer_id)] = {
            #     "id": offer_id,
            #     "filename": filename,
            #     "name": name,
            #     "geo": geo,
            # }
            print(f"[{offer_id}] {filename} — {len(data)} bytes, geo={geo}")
        except Exception as e:
            failed.append({"id": offer_id, "name": name, "error": str(e)})
            print(f"[{offer_id}] FAILED: {e}")
    
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone. Saved {len(mapping)} offers. Failed: {len(failed)}")
    if failed:
        print("Failed ids:", [x["id"] for x in failed])
    
    return mapping, failed

######### Работа с новым Keitaro #########
######### Заливка офферов #########

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

def get_group_map_new():
    groups = get_groups()
    return {g["name"][:2].lower(): g["id"] for g in groups}

def create_group(name):
    payload = {
        "name": name,
        "type": "offers",
    }
    response = httpx.post(
        f"{KEITARO_URL}/admin_api/v1/groups",
        headers={"Api-Key": KEITARO_API_KEY},
        json=payload,
    )
    response.raise_for_status()
    return response.json()

def upload_offer_page(archive_path, offer_name, group_id, funnel):
    
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
    if funnel:
        payload["values"] = [{"name": "funnel", "value": funnel}]

    response = httpx.post(
        f"{KEITARO_URL}/admin_api/v1/offers",
        headers={"Api-Key": KEITARO_API_KEY},
        json=payload,
    )

    response.raise_for_status()
    return response.json()

def upload_all_offers(mapping_path, archive_dir="offers_archives_old"):
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    group_map = get_group_map_new()
    
    # for offer_id, info in list(mapping.items())[:1]:
    for offer_id, info in mapping.items():
        filename = info["filename"]
        name = info["name"]
        geo = info["geo"]
        funnel = info["funnel"] if "funnel" in info else None
        
        # Determine group_id based on geo
        # group_id = get_group_id(geo)
        group_id = group_map.get(geo.lower() if geo else None)
        
        # if group_id is None:
        #     print(f"[{offer_id}] Skipping {filename}: No group found for geo '{geo}'")
        #     continue
        
        try:
            result = upload_offer_page(
                Path(archive_dir) / filename,
                name,
                group_id,
                funnel,
            )
            print(f"[{offer_id}] Uploaded: {filename} → Offer #{result['id']}")
        except Exception as e:
            print(f"[{offer_id}] FAILED to upload {filename}: {e}")

###################################################################
################### Работа со старыми Keitaro #####################
################### Загрузка лендингов ############################
###################################################################

def get_all_landings_old():
    response = httpx.get(
        f"{KEITARO_ASIA_URL}/admin_api/v1/landing_pages",
        headers={"Api-Key": KEITARO_ASIA_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def get_groups_old_landings():
    response = httpx.get(
        f"{KEITARO_ASIA_URL}/admin_api/v1/groups?type=landings",
        headers={"Api-Key": KEITARO_ASIA_API_KEY},
    )

    response.raise_for_status()

    return response.json()

def get_landing_group_map_old():
    groups = get_groups_old_landings()
    group_map = {}
    for group in groups:
        group_map[group["id"]] = group["name"]
    return group_map

def download_landing_archive(landing_id):
    for attempt in range(3):
        try:
            response = httpx.get(
                f"{KEITARO_ASIA_URL}/admin_api/v1/landing_pages/{landing_id}/download",
                headers={"Api-Key": KEITARO_ASIA_API_KEY},
                timeout=120.0,
            )
            response.raise_for_status()
            return response.content
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == 2:
                raise
            print(f"  retry {attempt+1} for offer {landing_id}: {e}")
            time.sleep(5)

def download_all_landings(out_dir="landing_archives_old", mapping_path="landing_archives_old/mapping_landings.json"):
    Path(out_dir).mkdir(exist_ok=True)
    
    landings = get_all_landings_old()
    group_map = get_landing_group_map_old()
    mapping = {}
    failed = []
    
    for landing in landings:
        landing_id = landing["id"]
        name = landing["name"]
        geo = group_map.get(landing["group_id"])
        filename = sanitize_filename(name) + "_sa.zip"
        
        try:
            data = download_landing_archive(landing_id)
            with open(Path(out_dir) / filename, "wb") as f:
                f.write(data)

            mapping[str(landing_id)] = {
                "id": landing_id,
                "filename": filename,
                "name": name,
                "geo": geo,
            }
            print(f"[{landing_id}] {filename} — {len(data)} bytes, geo={geo}")
        except Exception as e:
            failed.append({"id": landing_id, "name": name, "error": str(e)})
            print(f"[{landing_id}] FAILED: {e}")

    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone. Saved {len(mapping)} landings. Failed: {len(failed)}")
    if failed:
        print("Failed ids:", [x["id"] for x in failed])
    
    return mapping, failed

###################################################################
################### Работа с новым Keitaro ########################
################### Заливка лендингов #############################
###################################################################

def upload_landing_page(archive_path, landing_name, group_id):
    with open(archive_path, "rb") as file:
        archive = file.read()
        archive_b64 = base64.b64encode(archive).decode("utf-8")

    payload = {
        "name": landing_name,
        "group_id": group_id,
        "landing_type": "local",
        "action_type": "local_file",
        "archive": archive_b64,
    }

    response = httpx.post(
        f"{KEITARO_URL}/admin_api/v1/landing_pages",
        headers={"Api-Key": KEITARO_API_KEY},
        json=payload,
    )

    response.raise_for_status()
    return response.json()

def get_landing_group_map_new():
    response = httpx.get(
        f"{KEITARO_URL}/admin_api/v1/groups?type=landings",
        headers={"Api-Key": KEITARO_API_KEY},
    )
    response.raise_for_status()
    return {g["name"]: g["id"] for g in response.json()}

def upload_all_landings(mapping_path, archive_dir="landing_archives_old"):
    group_map = get_landing_group_map_new()
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    
    # for landing_id, info in list(mapping.items())[:1]:
    for landing_id, info in mapping.items():
        filename = info["filename"]
        name = info["name"]
        geo = info["geo"]
        
        group_id = group_map.get(geo)
        
        if group_id is None:
            print(f"[{landing_id}] Skipping {filename}: No group for geo '{geo}'")
            continue
        
        try:
            result = upload_landing_page(
                Path(archive_dir) / filename,
                name,
                group_id,
            )
            print(f"[{landing_id}] Uploaded: {filename} → Landing #{result['id']}")
        except Exception as e:
            print(f"[{landing_id}] FAILED to upload {filename}: {e}")