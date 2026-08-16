"""U1《数据侦探的第一步》：周数据小报起始代码

这是教学模拟数据。请不要在程序中输入姓名、成绩、健康、住址等敏感个人信息。
完成基础任务后，再尝试文件末尾的挑战任务。
"""

# 任务 1：选择你的主题。可改成“运动”“番茄钟”等。
topic = "阅读"
unit = "分钟"

# 任务 2：修改这 7 个模拟数据，或在教师允许的范围内替换为不含个人信息的数据。
weekly_minutes = [25, 35, 40, 15, 30, 50, 20]

# 任务 3：修改你的每日目标。
daily_goal = 30

print("=" * 36)
print(f"{topic}周数据小报")
print("=" * 36)
print(f"每日目标：{daily_goal} {unit}")
print(f"本周记录：{weekly_minutes}")
print("-" * 36)

# 任务 4：请先预测下方循环会做什么，再运行验证。
total_minutes = 0
goal_days = 0

day_number = 1
for minutes in weekly_minutes:
    print(f"第 {day_number} 天：{minutes} {unit}")

    # 任务 5：把当天数据累计到总量中。
    total_minutes += minutes

    # 任务 6：如果当天达到目标，就把达标天数加 1。
    if minutes >= daily_goal:
        goal_days += 1

    day_number += 1

# 任务 7：计算平均值。为什么要用 len(weekly_minutes)？
average_minutes = total_minutes / len(weekly_minutes)

print("-" * 36)
print(f"本周总{topic}量：{total_minutes} {unit}")
print(f"平均每天：{average_minutes:.1f} {unit}")
print(f"达标天数：{goal_days} 天 / {len(weekly_minutes)} 天")

# 任务 8：让程序给出一条简单建议。
if goal_days >= 5:
    print("建议：你的节奏比较稳定，可以尝试保持这个习惯。")
else:
    print("建议：可以从一个更容易坚持的小目标开始，例如每天增加 5 分钟。")

print("=" * 36)
print("数据边界提醒：这只是 7 条教学模拟记录，不能据此推断长期习惯或学习效果。")

# 挑战 A：将“达标天数”改为计算“连续达标的最长天数”。
# 挑战 B：将计算总量或达标天数的代码写成函数。
# 挑战 C：让用户用 input() 输入新的每日目标，再重新判断达标天数。
