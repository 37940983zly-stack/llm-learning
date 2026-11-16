# ============================================
# 毕业项目：全自动股票舆情 Agent
#
# 用法：
#   1. 编辑 股票清单.txt（你关注的股票，每行一只）
#   2. 编辑 今日新闻.txt（每天粘贴当日新闻标题/摘要）
#   3. python3 grad_agent.py → 生成 复盘报告_日期.txt
#
# 用到的全部知识：
#   模块一：API调用、结构化输出、token计价
#   模块二：提示词六件套、Few-shot、CoT边界
#   模块三：RAG检索、双层拒答（检索层+生成层核对）
#   模块四：Agent Loop、按钮、预算
#   模块五：文件操作
# ============================================

import urllib.request, urllib.error, json, math, os, datetime

with open("key.txt") as f:
    my_key = f.read().strip()

def 调模型(白板, 工具=None, 温度=0.3):
    卡片 = {"model": "glm-4.5-flash", "temperature": 温度, "messages": 白板}
    if 工具:
        卡片["tools"] = 工具
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(卡片).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    for 第几次 in range(3):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())["choices"][0]["message"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500) and 第几次 < 2:
                import time; time.sleep(5); continue
            print("服务器拒绝了:", e.code, e.read().decode()[:100])
            raise SystemExit

def 问(白板, 温度=0.3):
    消息 = 调模型(白板, 温度=温度)
    return 消息["content"]

# ===== 加载配置 =====
def 读文件安全(路径, 默认内容=""):
    try:
        with open(路径) as f:
            return f.read().strip()
    except FileNotFoundError:
        with open(路径, "w") as f:
            f.write(默认内容)
        return 默认内容

股票清单 = [行.strip() for 行 in 读文件安全("股票清单.txt", "贵州茅台\n腾讯控股\n宁德时代").split("\n") if 行.strip()]
今日新闻 = 读文件安全("今日新闻.txt", "（暂无新闻，请编辑 今日新闻.txt 填入今日新闻标题）")
今日 = datetime.date.today().strftime("%Y-%m-%d")

print(f"=== 毕业项目：股票舆情 Agent ===")
print(f"日期：{今日}")
print(f"关注股票：{', '.join(股票清单)}")
print(f"今日新闻：{len(今日新闻)} 字\n")

# ===== 模拟行情（真实场景可接行情 API，此处用上一次调用结果）=====
模拟行情 = {"贵州茅台": "+2.5%", "腾讯控股": "-1.2%", "宁德时代": "-3.1%"}
行情文本 = "\n".join(f"  {名}：{模拟行情.get(名, '待查')}" for 名 in 股票清单)

# ===== Agent 主循环：逐股分析 =====
报告 = []
报告.append(f"📊 股票复盘报告 | {今日}\n")
报告.append(f"{'='*50}\n")

总token = 0

for 名 in 股票清单:
    print(f"分析中：{名} ...")

    # 步骤1：从今日新闻中提取与该股相关的信息（RAG思路：先检索再生成）
    新闻白板 = [
        {"role": "system", "content": "你是新闻筛选助手。只输出 JSON，格式：{\"相关新闻\": [\"条目1\", ...], \"情绪\": \"利好/利空/中性\"}。如果新闻列表中没有与该股票直接相关的内容，返回空数组和中性。"},
        {"role": "user", "content": f"股票：{名}\n\n今日新闻列表：\n{今日新闻}\n\n请筛选出与 {名} 直接相关的新闻条目，并判断整体情绪。"}
    ]
    try:
        新闻结果_raw = 问(新闻白板, 温度=0.1)
        新闻结果 = json.loads(新闻结果_raw)
        相关 = 新闻结果.get("相关新闻", [])
        情绪 = 新闻结果.get("情绪", "中性")
    except:
        相关 = []
        情绪 = "中性"

    # 步骤2：综合分析（生成复盘）
    分析白板 = [
        {"role": "system", "content":
            f"你是小于的股票复盘助手，风格稳健谨慎、不吹不黑。"
            f"小于的投资风格：稳健，不追热点，注重风险提示。"
            f"今天日期：{今日}。"
            f"输出格式：一行复盘（不超过 60 字），格式为'股票名｜涨跌幅｜情绪｜一句话点评'。"
            f"如果今日新闻中没有该股的直接信息，点评中注明'今日无直接新闻'。"
            f"绝不编造新闻内容。"},
        {"role": "user", "content":
            f"股票：{名}\n"
            f"今日涨跌幅：{模拟行情.get(名, '待查')}\n"
            f"相关新闻：{json.dumps(相关, ensure_ascii=False) if 相关 else '（无直接相关新闻）'}\n"
            f"新闻情绪：{情绪}\n"
            f"请生成一行复盘。"}
    ]
    复盘行 = 问(分析白板)
    报告.append(f"  {复盘行}\n")
    print(f"  → {复盘行}")

# ===== 总览 =====
报告.append(f"{'='*50}\n")
报告.append("📌 明日关注\n")

总览白板 = [
    {"role": "system", "content":
        "你是小于的股票复盘助手。根据以上所有个股分析，生成一段'明日关注'总结（不超过 100 字），"
        "指出：1.需要重点观察的股票及原因 2.整体风险提示。风格稳健，不吹不黑。"},
    {"role": "user", "content": "\n".join(报告)}
]
明日关注 = 问(总览白板)
报告.append(f"  {明日关注}\n")

# ===== 写文件 =====
报告文件 = f"复盘报告_{今日}.txt"
报告内容 = "\n".join(报告)
with open(报告文件, "w") as f:
    f.write(报告内容 + f"\n\n（由毕业项目 Agent 自动生成 | {datetime.datetime.now().strftime('%H:%M')}）\n")

print(f"\n{'='*50}")
print(f"✅ 报告已保存：{报告文件}")
print(f"\n{报告内容}")
