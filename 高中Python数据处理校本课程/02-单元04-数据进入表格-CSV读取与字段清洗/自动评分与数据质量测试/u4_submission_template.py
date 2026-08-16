"""U4 自动评分提交模板。只修改 TODO，不改函数名和参数。"""
import csv


def read_rows(path):
    """读取 CSV，返回字典记录列表。"""
    rows = []
    # TODO：使用 csv.DictReader 读取 path，并将每行复制到 rows。
    return rows


def clean_rows(rows):
    """返回 (valid_rows, issues, stats)。"""
    valid_rows = []
    issues = []
    # TODO：检查 visits 和 minutes 的空值、空格、整数转换和负数。
    # TODO：保留问题记录的 record_index、field、raw_value、reason。
    stats = {
        "raw_count": len(rows),
        "valid_count": len(valid_rows),
        "issue_count": len(issues),
        "review_count": 0,
    }
    return valid_rows, issues, stats


def group_summary(valid_rows):
    """返回按 space 分组的汇总字典。"""
    # TODO：每组至少包含 valid_count、total_visits、total_minutes、average_minutes。
    return {}
