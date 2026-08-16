"""U5 自动评分参考提交。"""


def summarize(values):
    if not values:
        return {"mean": None, "median": None, "count": 0, "total": 0}
    numbers = sorted(float(value) for value in values)
    count = len(numbers)
    total = sum(numbers)
    middle = count // 2
    median = numbers[middle] if count % 2 else (numbers[middle - 1] + numbers[middle]) / 2
    return {
        "mean": total / count,
        "median": median,
        "count": count,
        "total": total,
    }


def choose_chart(question_type, data_shape):
    if data_shape == "time_series":
        return "line"
    if question_type == "composition":
        return "pie"
    return "bar"


def build_story(question, values, question_type, data_shape):
    stats = summarize(values)
    chart_type = choose_chart(question_type, data_shape)
    return {
        "question": question,
        "statistic": "mean",
        "chart_type": chart_type,
        "count": stats["count"],
        "denominator": f"{stats['count']}条有效教学模拟记录",
        "observation": f"这组模拟记录的平均值为 {stats['mean']}",
        "boundary": "不能据此断言真实校园中的长期规律或因果关系",
    }
