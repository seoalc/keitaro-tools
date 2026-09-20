import re

def replace_phone_input(content, new_phone_html):
    pattern_with_label = re.compile(
        r'<label\b[^>]*>(?:(?!<input\b).)*<input\b[^>]*\bname=["\']phone["\'][^>]*/?>(?:(?!</label>).)*?</label>',
        re.IGNORECASE | re.DOTALL
    )
    pattern_without_label = re.compile(r'<input\b[^>]*\bname=["\']phone["\'][^>]*/?>', re.IGNORECASE)

    if pattern_with_label.search(content):
        new_content = pattern_with_label.sub(new_phone_html, content, count=1)
        return new_content, "with_label"
    if pattern_without_label.search(content):
        new_content = pattern_without_label.sub(new_phone_html, content, count=1)
        return new_content, "without_label"
    return content, "not_found"