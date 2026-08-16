"""U3《数据变形记：列表与批量清洗》参考实现。

数据均为教学模拟数据。程序保留问题记录与原因，不把无法判断的内容擅自改成 0 或直接删除。
"""


raw_records = [
    {"record_id": "R01", "day": "周一", "minutes": "25"},
    {"record_id": "R02", "day": "周二", "minutes": " 35 "},
    {"record_id": "R03", "day": "周三", "minutes": ""},
    {"record_id": "R04", "day": "周四", "minutes": "30分钟"},
    {"record_id": "R05", "day": "周二", "minutes": "35"},
    {"record_id": "R06", "day": "周五", "minutes": "abc"},
    {"record_id": "R07", "day": "周六", "minutes": "0"},
]


def clean_minutes(raw_value):
    """把可修复的分钟格式转为非负整数；否则返回问题原因。"""
    text = str(raw_value).strip().replace("分钟", "")
    if text == "":
        return None, "缺失值"
    if not text.isdigit():
        return None, "无法转为数字"

    minutes = int(text)
    if minutes < 0:
        return None, "不应为负数"
    return minutes, None


def transform_records(records):
    """返回清洗后的记录列表和问题记录列表，不修改原始列表。"""
    clean_records = []
    issues = []

    for record in records:
        minutes, issue = clean_minutes(record["minutes"])
        if issue is None:
            clean_records.append(
                {
                    "record_id": record["record_id"],
                    "day": record["day"],
                    "minutes": minutes,
                }
            )
        else:
            issues.append(
                {
                    "record_id": record["record_id"],
                    "reason": issue,
                    "raw_value": record["minutes"],
                }
            )

    return clean_records, issues


def summarize(clean_records):
    """汇总有效记录，并始终返回相同结构的结果。"""
    if len(clean_records) == 0:
        return {"count": 0, "total": 0, "average": 0, "max": None, "min": None}

    values = []
    total = 0
    for record in clean_records:
        value = record["minutes"]
        values.append(value)
        total += value

    return {
        "count": len(clean_records),
        "total": total,
        "average": total / len(clean_records),
        "max": max(values),
        "min": min(values),
    }


def print_quality_report(raw_records, clean_records, issues, summary):
    """展示汇总与质量日志，强调结果必须带处理边界。"""
    print("=" * 60)
    print("数据变形记：教学模拟批量清洗报告")
    print("=" * 60)
    print(f"原始记录数：{len(raw_records)}")
    print(f"有效记录数：{summary['count']}")
    print(f"问题记录数：{len(issues)}")
    print(f"有效记录总分钟数：{summary['total']}")
    print(f"有效记录平均分钟数：{summary['average']:.1f}")
    print(f"最大/最小分钟数：{summary['max']} / {summary['min']}")
    print("-" * 60)
    print("清洗后的有效记录：")
    for record in clean_records:
        print(record)
    print("-" * 60)
    print("质量日志（未进入汇总）：")
    for issue in issues:
        print(issue)
    print("=" * 60)
    print("边界说明：R05 与 R02 是否为重复记录不能仅凭当前字段决定，需要查询来源或更多标识信息。")


clean_records, issues = transform_records(raw_records)
summary = summarize(clean_records)
print_quality_report(raw_records, clean_records, issues, summary)
