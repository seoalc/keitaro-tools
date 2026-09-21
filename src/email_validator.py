from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"

def load_asset(name):
    return (ASSETS_DIR / name).read_text(encoding="utf-8")

EMAIL_RULES = [
    {
        "id": "email_validation_js",
        "type": "insert_before",
        "target": "</body>",
        "content": '<script src="files/email-validation.js"></script>',
        "marker": "email-validation.js",
    },
]

EMAIL_ASSETS = {
    "files/email-validation.js": load_asset("email-validation.js"),
}