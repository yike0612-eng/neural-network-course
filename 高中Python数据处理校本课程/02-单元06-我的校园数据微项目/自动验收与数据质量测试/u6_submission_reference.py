"""U6 自动验收参考实现：阅读空间模拟数据微项目。"""


def project_metadata():
    return {
        "question": "在教学模拟有效记录中，东区与西区的平均阅读分钟数如何比较？",
        "approved_data": True,
        "personal_data_collected": False,
        "data_scope": "教师提供的6条教学模拟阅读空间记录，不代表真实学生规律。",
        "core_metric": "各空间有效记录的平均阅读分钟数",
        "chart_type": "bar",
        "unit": "分钟",
        "recommendation": "可以先用下一轮教学模拟记录复核空间差异，再决定是否调整阅读提示。",
        "boundary": "不能据此断言某个空间更适合所有学生，也不能推断阅读分钟数导致其他结果。",
    }


def _issue(raw_record, field, raw_value, reason):
    return {
        "ok": False,
        "record": None,
        "issue": {
            "record_index": raw_record.get("__index__", -1),
            "field": field,
            "raw_value": raw_value,
            "reason": reason,
        },
    }


def clean_record(raw_record):
    category_raw = raw_record.get("category")
    value_raw = raw_record.get("value")
    period_raw = raw_record.get("period", "")

    if category_raw is None or not str(category_raw).strip():
        return _issue(raw_record, "category", category_raw, "类别为空")
    category = str(category_raw).strip()

    if value_raw is None or not str(value_raw).strip():
        return _issue(raw_record, "value", value_raw, "数值为空")
    text = str(value_raw).strip().replace("分钟", "")
    try:
        value = float(text)
    except ValueError:
        return _issue(raw_record, "value", value_raw, "数值无法转换")
    if value < 0:
        return _issue(raw_record, "value", value_raw, "数值不能为负")

    return {
        "ok": True,
        "record": {
            "category": category,
            "value": int(value) if value.is_integer() else value,
            "period": str(period_raw).strip(),
        },
        "issue": None,
    }


def process_records(raw_records):
    valid = []
    issues = []
    for index, original in enumerate(raw_records):
        item = dict(original)
        item["__index__"] = index
        result = clean_record(item)
        if result["ok"]:
            valid.append(result["record"])
        else:
            issues.append(result["issue"])
    stats = {
        "raw_count": len(raw_records),
        "valid_count": len(valid),
        "issue_count": len(issues),
    }
    return valid, issues, stats


def group_summary(valid_records):
    groups = {}
    for record in valid_records:
        category = record["category"]
        if category not in groups:
            groups[category] = {"valid_count": 0, "total_value": 0}
        groups[category]["valid_count"] += 1
        groups[category]["total_value"] += record["value"]
    for item in groups.values():
        item["average_value"] = item["total_value"] / item["valid_count"]
    return groups


def build_chart_spec(summary):
    labels = list(summary.keys())
    values = [summary[label]["average_value"] for label in labels]
    return {
        "chart_type": "bar",
        "title": "教学模拟记录中各空间平均阅读分钟数",
        "x_label": "阅读空间",
        "y_label": "平均阅读分钟数",
        "unit": "分钟",
        "labels": labels,
        "values": values,
        "scope_note": "仅基于教师提供的教学模拟有效记录，不代表真实学生规律。",
    }
