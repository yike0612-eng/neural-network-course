"""U4 自动评分参考提交。"""
import csv


def read_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _to_nonnegative_int(raw_value):
    text = str(raw_value).strip()
    if text == "":
        return None, "缺失值"
    if not text.isdigit():
        return None, "无法转为非负整数"
    return int(text), None


def clean_rows(rows):
    valid_rows = []
    issues = []
    seen_keys = set()

    for index, row in enumerate(rows, start=1):
        current = dict(row)
        row_issues = []
        cleaned = dict(row)
        for field in ("visits", "minutes"):
            value, reason = _to_nonnegative_int(row.get(field, ""))
            if reason:
                row_issues.append({
                    "record_index": index,
                    "field": field,
                    "raw_value": row.get(field, ""),
                    "reason": reason,
                })
            else:
                cleaned[field] = value

        duplicate_key = tuple(row.get(field, "") for field in ("date", "space", "visits", "minutes"))
        if duplicate_key in seen_keys:
            row_issues.append({
                "record_index": index,
                "field": "row",
                "raw_value": str(current),
                "reason": "按整行字段规则疑似重复，需复核",
            })
        seen_keys.add(duplicate_key)

        if row_issues:
            issues.extend(row_issues)
        else:
            valid_rows.append(cleaned)

    stats = {
        "raw_count": len(rows),
        "valid_count": len(valid_rows),
        "issue_count": len(issues),
        "review_count": sum("复核" in item["reason"] for item in issues),
    }
    return valid_rows, issues, stats


def group_summary(valid_rows):
    groups = {}
    for row in valid_rows:
        group = row["space"]
        item = groups.setdefault(group, {
            "valid_count": 0,
            "total_visits": 0,
            "total_minutes": 0,
            "average_minutes": None,
        })
        item["valid_count"] += 1
        item["total_visits"] += int(row["visits"])
        item["total_minutes"] += int(row["minutes"])

    for item in groups.values():
        item["average_minutes"] = item["total_minutes"] / item["valid_count"] if item["valid_count"] else None
    return groups
