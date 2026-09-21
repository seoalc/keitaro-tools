import re

def apply_rules(content: str, rules: list[dict]) -> tuple[str, list[dict]]:
    log = []
    new_content = content
    
    for rule in rules:
        rule_id = rule["id"]
        
        # 1. Идемпотентность
        marker = rule.get("marker")
        if marker and marker in new_content:
            log.append({"rule_id": rule_id, "status": "skipped"})
            continue
        
        # 2. Диспетчер по типу
        rule_type = rule["type"]
        
        if rule_type == "insert_before":
            target = rule["target"]
            if target in new_content:
                new_content = new_content.replace(target, rule["content"] + "\n" + target, 1)
                log.append({"rule_id": rule_id, "status": "applied"})
            else:
                log.append({"rule_id": rule_id, "status": "not_found"})
        
        elif rule_type == "replace_regex":
            applied = False
            for pattern_str in rule["patterns"]:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.DOTALL)
                if pattern.search(new_content):
                    new_content = pattern.sub(rule["replacement"], new_content, count=1)
                    log.append({"rule_id": rule_id, "status": "applied"})
                    applied = True
                    break
            if not applied:
                log.append({"rule_id": rule_id, "status": "not_found"})
        
        else:
            log.append({"rule_id": rule_id, "status": "unknown_type"})
    
    return new_content, log