"""U5 自动评分提交模板。只修改 TODO，不修改函数名和参数。"""


def summarize(values):
    """返回 mean、median、count、total。"""
    # TODO：处理空列表，并计算基本统计量。
    return {"mean": None, "median": None, "count": 0, "total": 0}


def choose_chart(question_type, data_shape):
    """返回 bar、line 或 pie。"""
    # TODO：根据问题和数据形状选择图表。
    return ""


def build_story(question, values, question_type, data_shape):
    """返回一页数据故事的结构化说明。"""
    stats = summarize(values)
    return {
        "question": question,
        "statistic": "",  # TODO
        "chart_type": choose_chart(question_type, data_shape),
        "count": stats["count"],
        "denominator": "",  # TODO
        "observation": "",  # TODO
        "boundary": "",  # TODO
    }
