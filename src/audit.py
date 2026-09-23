import io
import zipfile
from process_offer import download_offer_archive, get_all_offers
from kt_files import get_html_php_files, walk_files, get_offer_files_structure

# Список маркеров, которые проверяем
MARKERS_TO_CHECK = ["{_back}", "{_fbpixel}", "{_phonemacros}", "window.back"]

def audit_offer(offer_id):
    """Возвращает dict {marker: count} для index.php (или всех html/php)."""
    data = download_offer_archive(offer_id)
    
    counts = {m: 0 for m in MARKERS_TO_CHECK}
    
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            # только index.php / html / php
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in ("html", "htm", "php"):
                continue
            content = z.read(name).decode("utf-8", errors="replace")
            for m in MARKERS_TO_CHECK:
                counts[m] += content.count(m)
    
    return counts


def audit_all_offers():
    offers = get_all_offers()
    problem = []
    
    for offer in offers:
        oid = offer["id"]
        try:
            counts = audit_offer(oid)
            # проверяем: любой маркер > 1 — проблема
            bad = {m: c for m, c in counts.items() if c > 1}
            if bad:
                problem.append((oid, bad))
                print(f"[{oid}] DUPLICATES: {bad}")
            else:
                print(f"[{oid}] OK")
        except Exception as e:
            print(f"[{oid}] ERROR: {e}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total offers: {len(offers)}")
    print(f"Problem offers: {len(problem)}")
    if problem:
        print("\nProblem IDs:")
        for oid, bad in problem:
            print(f"  {oid}: {bad}")
    
    return problem


# Запуск
# problems = audit_all_offers()