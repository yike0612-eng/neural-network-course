"""U6《校园数据微项目》自动验收提交模板。

把本文件复制为 u6_submission.py，再逐步完成五个函数。
课堂提交必须只使用教师批准的教学模拟或公开脱敏数据。
"""


def project_metadata():
    """返回项目的范围与责任声明。"""
    return {
        "question": "请填写一个可回答的小问题",
        "approved_data": False,
        "personal_data_collected": False,
        "data_scope": "请填写数据范围",
        "core_metric": "请填写一项核心指标",
        "chart_type": "bar",  # bar 或 line
        "unit": "请填写单位",
        "recommendation": "请填写一条谨慎建议",
        "boundary": "请填写一条不能据此断言的边界",
    }


def clean_record(raw_record):
    """把单条原始记录转换为统一测试字段。

    有效记录返回：
    {"ok": True, "record": {"category": str, "value": number, "period": str}, "issue": None}

    问题记录返回：
    {"ok": False, "record": None,
     "issue": {"record_index": int, "field": str, "raw_value": object, "reason": str}}
    """
    # TODO：先复制原始值，再清理类别、数值和时间/顺序字段。
    # TODO：空值、无效文本、负值等应进入问题日志，不要静默删除。
    return {
        "ok": False,
        "record": None,
        "issue": {
            "record_index": raw_record.get("__index__", -1),
            "field": "unknown",
            "raw_value": None,
            "reason": "尚未完成 clean_record",
        },
    }


def process_records(raw_records):
    """批量处理记录，返回 valid, issues, stats。

    stats 至少包含 raw_count、valid_count、issue_count。
    不要修改 raw_records 或其中原始字典。
    """
    valid = []
    issues = []
    for index, original in enumerate(raw_records):
        item = dict(original)
        item["__index__"] = index
        result = clean_record(item)
        if result.get("ok"):
            valid.append(result.get("record"))
        else:
            issues.append(result.get("issue"))
    stats = {
        "raw_count": len(raw_records),
        "valid_count": len(valid),
        "issue_count": len(issues),
    }
    return valid, issues, stats


def group_summary(valid_records):
    """按 category 汇总，返回每类的有效数、总量和平均值。"""
    # TODO：只使用有效记录完成汇总。
    return {}


def build_chart_spec(summary):
    """返回主图规格字典，不要求本函数真正绘图。

    至少包含 chart_type、title、x_label、y_label、unit、labels、values、scope_note。
    labels 和 values 必须来自 summary，长度必须一致。
    """
    return {
        "chart_type": "bar",
        "title": "请填写标题",
        "x_label": "请填写横轴",
        "y_label": "请填写纵轴",
        "unit": "请填写单位",
        "labels": [],
        "values": [],
        "scope_note": "请填写数据范围或边界",
    }
