import re
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"

def load_asset(name):
    return (ASSETS_DIR / name).read_text(encoding="utf-8")

NEW_PHONE_HTML = '''<div class="intgrtn-input-holder intgrtn-input-holder-phone">
        <div class="phone-wrapper">
          <label>Teléfono</label>
            <input class="intgrtn-input phonelist phone-valid" id="phone" type="tel" name="phone" placeholder="Número de teléfono" required autocomplete="off">
            <input name="full_phone" class="full_phone" type="hidden" value="">
            <div class="error-message" id="error-phone-es">Por favor ingresa un número de teléfono válido</div>
        </div>
    </div>'''

PHONE_RULES = [
    {
        "id": "intl_tel_css",
        "type": "insert_before",
        "target": "</head>",
        "content": '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/css/intlTelInput.min.css">\n<link rel="stylesheet" href="files/input-styles.css">',
        "marker": "intlTelInput.min.css",
    },
    {
        "id": "intl_tel_js",
        "type": "insert_before",
        "target": "</body>",
        "content": '<script src="https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/intlTelInput.min.js"></script>\n<script src="https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js"></script>\n<script src="files/input-app.js"></script>',
        "marker": "intlTelInput.min.js",
    },
    {
        "id": "phone_replace",
        "type": "replace_regex",
        "patterns": [
            # 1. label оборачивает input
            r'<label\b[^>]*>(?:(?!<input\b).)*<input\b[^>]*\bname=["\']phone["\'][^>]*/?>(?:(?!</label>).)*?</label>',
            
            # 2. label закрывается перед input
            r'<label\b[^>]*>(?:(?!</label>).)*?</label>\s*<input\b[^>]*\bname=["\']phone["\'][^>]*/?>',
            
            # 3. только input
            r'<input\b[^>]*\bname=["\']phone["\'][^>]*/?>',
        ],
        "replacement": NEW_PHONE_HTML,
        "marker": "intgrtn-input-holder-phone",
        "required": True,
    },
]

PHONE_ASSETS = {
    "files/input-styles.css": load_asset("input-styles.css"),
    "files/input-app.js": load_asset("input-app.js"),
}

# def replace_phone_input(content, new_phone_html):
#     pattern_with_label = re.compile(
#         r'<label\b[^>]*>(?:(?!<input\b).)*<input\b[^>]*\bname=["\']phone["\'][^>]*/?>(?:(?!</label>).)*?</label>',
#         re.IGNORECASE | re.DOTALL
#     )
#     pattern_without_label = re.compile(r'<input\b[^>]*\bname=["\']phone["\'][^>]*/?>', re.IGNORECASE)

#     if pattern_with_label.search(content):
#         new_content = pattern_with_label.sub(new_phone_html, content, count=1)
#         return new_content, "with_label"
#     if pattern_without_label.search(content):
#         new_content = pattern_without_label.sub(new_phone_html, content, count=1)
#         return new_content, "without_label"
#     return content, "not_found"