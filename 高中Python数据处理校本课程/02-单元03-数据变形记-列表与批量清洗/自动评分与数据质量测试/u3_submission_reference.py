"""U3 自动评分参考提交。"""


def clean_minutes(raw_value):
    text = str(raw_value).strip().replace("分钟", "")
    if text == "":
        return None, "缺失值"
    if not text.isdigit():
        return None, "无法转为非负整数"

    minutes = int(text)
    return minutes, None


def transform_records(raw_records):
    clean_records = []
    issues = []

    for record in raw_records:
        minutes, issue = clean_minutes(record["minutes"])
        if issue is None:
            clean_records.append({
                "record_id": record["record_id"],
                "day": record["day"],
                "minutes": minutes,
            })
        else:
            issues.append({
                "record_id": record["record_id"],
                "raw_value": record["minutes"],
                "reason": issue,
            })

    return clean_records, issues


def summarize_records(clean_records, issues):
    total_minutes = sum(record["minutes"] for record in clean_records)
    valid_count = len(clean_records)
    return {
        "valid_count": valid_count,
        "issue_count": len(issues),
        "total_minutes": total_minutes,
        "average_minutes": total_minutes / valid_count if valid_count else None,
    }
