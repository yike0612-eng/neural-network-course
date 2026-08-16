"""U3《数据变形记：列表与批量清洗》起始代码。

数据均为教学模拟数据。请不要替换为真实同学的姓名、成绩、健康、住址或其他敏感个人信息。
完成函数中的 TODO 后，再运行文件查看批量处理结果。
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
    """把可修复的分钟格式转为整数；不能确定的值返回问题原因。"""
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
    """将原始记录分为有效记录和质量日志；不要修改 records 本身。"""
    clean_records = []
    issues = []

    for record in records:
        minutes, issue = clean_minutes(record["minutes"])

        if issue is None:
            # TODO 1：把本条清洗后的记录加入 clean_records。
            # clean_records.append({...})
            pass
        else:
            # TODO 2：把本条问题记录加入 issues，保留 record_id、reason、raw_value。
            # issues.append({...})
            pass

    return clean_records, issues


def summarize(clean_records):
    """返回有效记录的数量、总量和平均值；空列表时三个值均为 0。"""
    if len(clean_records) == 0:
        return {"count": 0, "total": 0, "average": 0}

    total = 0
    for record in clean_records:
        # TODO 3：累计每条有效记录的 minutes。
        pass

    return {
        "count": len(clean_records),
        "total": total,
        "average": total / len(clean_records),
    }


clean_records, issues = transform_records(raw_records)
summary = summarize(clean_records)

print("=" * 52)
print("数据变形记：教学模拟批量清洗")
print("=" * 52)
print(f"原始记录数：{len(raw_records)}")
print(f"有效记录数：{summary['count']}")
print(f"问题记录数：{len(issues)}")
print(f"总分钟数：{summary['total']}")
print(f"平均分钟数：{summary['average']:.1f}")
print("-" * 52)
print("问题记录（完成 TODO 后应在此显示）：")
for issue in issues:
    print(issue)
print("=" * 52)
print("提醒：清洗规则只能处理已约定的格式问题；缺失、重复或异常来源仍可能需要人工复核。")
