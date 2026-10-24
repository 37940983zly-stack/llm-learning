# ============================================
# 项目②考卷自动评分：跑 20 题，出报告
#
# 读 考卷.txt（每行：预期|题目），逐题走 rag_agent 同款流程，
# 判断实际路径（命中/拒答/股价/无关），与预期比对，最后出四类正确率+误答率。
#
# 跑法：python3 rag_eval.py（全程约 4 分钟，每题之间歇 4 秒防限速）
# （函数与 rag_agent.py 相同——真实工程会用 import 复用，那招后面教）
# ============================================

import urllib.request, urllib.error, json, math, time

with open("key.txt") as f:
    my_key = f.read().strip()

def 调接口(地址, 卡片):
    # 自动重试：服务器偶发抖动（500/429）时歇 5 秒再试，最多 3 次——真实系统的标配
    for 第几次 in range(3):
        req = urllib.request.Request(
            地址, data=json.dumps(卡片).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            原话 = e.read().decode()
            if e.code in (429, 500) and 第几次 < 2:
                print(f"  （服务器抖了一下（{e.code}），歇 5 秒重试……）")
                time.sleep(5)
                continue
            print("服务器拒绝了，状态码：", e.code, "原话：", 原话)
            raise SystemExit

def 做指纹(句子们):
    return [d["embedding"] for d in
            调接口("https://open.bigmodel.cn/api/paas/v4/embeddings",
                    {"model": "embedding-3", "input": 句子们})["data"]]

def 相似度(a, b):
    点积 = sum(x * y for x, y in zip(a, b))
    长a = math.sqrt(sum(x * x for x in a))
    长b = math.sqrt(sum(y * y for y in b))
    return 点积 / (长a * 长b)

def 问模型(白板, 工具=None, 温度=0.3):
    卡片 = {"model": "glm-4.5-flash", "temperature": 温度, "messages": 白板}
    if 工具:
        卡片["tools"] = 工具
    return 调接口("https://open.bigmodel.cn/api/paas/v4/chat/completions", 卡片)["choices"][0]["message"]

with open("知识库.txt") as f:
    知识库 = [行.strip() for 行 in f if 行.strip()]
知识库指纹们 = 做指纹(知识库)
拒答线 = 0.40

def 查舆情知识库(问题):
    问题指纹 = 做指纹([问题])[0]
    排名 = sorted(range(len(知识库)), key=lambda i: -相似度(问题指纹, 知识库指纹们[i]))
    最高分 = 相似度(问题指纹, 知识库指纹们[排名[0]])
    if 最高分 < 拒答线:
        return None, 最高分        # None = 库里没有
    候选 = [知识库[i] for i in 排名[:5]]
    编号清单 = "".join(f"[{i+1}] {条}\n" for i, 条 in enumerate(候选))
    精排白板 = [
        {"role": "system", "content": "你是检索质量审核员，只输出 JSON。"},
        {"role": "user", "content": "候选资料：\n" + 编号清单 + "问题：" + 问题 +
            '\n挑出最能回答问题的2条，只输出 {"选择":[编号,编号]}'},
    ]
    选择 = json.loads(问模型(精排白板, 温度=0.1)["content"])["选择"]
    精选 = [候选[i - 1] for i in 选择 if 0 < i <= len(候选)][:2]
    return "".join(f"[{i+1}] {条}\n" for i, 条 in enumerate(精选)), 最高分

def 查股价(股票名):
    行情 = {"贵州茅台": 1650.5, "腾讯控股": 385.2, "宁德时代": 188.7}
    if 股票名 in 行情:
        return f"{股票名} 当前价格 {行情[股票名]} 元"
    return f"没有 {股票名} 的数据"

按钮说明书 = [
    {"type": "function", "function": {
        "name": "查舆情知识库",
        "description": "查询野生动植物网络违法舆情知识库。涉及舆情、举报、违法案件、保护动物的问题用它。",
        "parameters": {"type": "object",
                       "properties": {"问题": {"type": "string"}},
                       "required": ["问题"]}}},
    {"type": "function", "function": {
        "name": "查股价",
        "description": "查询股票当前价格。可查：贵州茅台、腾讯控股、宁德时代。",
        "parameters": {"type": "object",
                       "properties": {"股票名": {"type": "string"}},
                       "required": ["股票名"]}}},
]
真按钮 = {"查舆情知识库": 查舆情知识库, "查股价": 查股价}

def 判路径(问题):
    """走一遍 rag_agent 流程，返回（实际路径, 最终回答, 附加信息）"""
    白板 = [
        {"role": "system", "content":
            "你是助手，身边有两个按钮（见工具清单）。该查资料/查股价就按按钮；与两者都无关的问题就直接回答，不要硬按。"},
        {"role": "user", "content": 问题},
    ]
    按过的按钮 = []
    for _ in range(3):
        消息 = 问模型(白板, 工具=按钮说明书)
        if not 消息.get("tool_calls"):
            回答 = 消息["content"]
            if "查舆情知识库" in 按过的按钮:
                路径 = "命中" if 检索到内容 else "拒答"
            elif "查股价" in 按过的按钮:
                路径 = "股价"
            else:
                路径 = "无关"
            return 路径, 回答, 按过的按钮
        白板.append(消息)
        检索到内容 = False
        for 喊话 in 消息["tool_calls"]:
            按钮名 = 喊话["function"]["name"]
            参数 = json.loads(喊话["function"]["arguments"])
            按过的按钮.append(按钮名)
            if 按钮名 == "查舆情知识库":
                结果, 分数 = 查舆情知识库(**参数)
                检索到内容 = 结果 is not None
                结果文本 = 结果 if 结果 else f"知识库中无相关资料（最高相似度 {分数:.3f}）。"
            else:
                结果文本 = 查股价(**参数)
            白板.append({"role": "tool", "tool_call_id": 喊话["id"], "content": 结果文本})
    return "超限", "按钮按太多次", 按过的按钮

# ====== 读考卷，逐题判分 ======
with open("考卷.txt") as f:
    考卷 = [行.strip() for 行 in f
            if 行.strip() and not 行.strip().startswith("#")]

成绩 = {k: [0, 0] for k in ["命中", "拒答", "股价", "无关"]}   # [对, 总]
误答清单 = []

print(f"考卷共 {len(考卷)} 题，开跑（每题间隔 4 秒防限速，全程约几分钟）……\n")

for 序号, 行 in enumerate(考卷, 1):
    零件 = 行.split("|", 1)
    if len(零件) != 2:
        print(f"{序号:2d}. [跳过] 这行格式不对（缺竖线 | ）：{行}")
        continue                   # 一行坏题不该拖垮整场考试——跳过并警告，继续跑
    预期, 题目 = 零件[0].strip(), 零件[1].strip()
    try:
        实际, 回答, 按钮 = 判路径(题目.strip())
    except Exception as e:
        实际, 回答, 按钮 = "出错", str(e), []
    对错 = "✓" if 实际 == 预期 else "✗"
    成绩[预期][1] += 1
    if 实际 == 预期:
        成绩[预期][0] += 1
    else:
        if 预期 == "拒答" and 实际 in ("命中", "无关"):
            误答清单.append(题目.strip())          # 该拒没拒=编答案的嫌疑
    print(f"{序号:2d}. [{对错}] 预期{预期} 实际{实际}｜{题目.strip()}")
    print(f"     回答摘要：{回答[:60]}……")
    if 序号 < len(考卷):
        time.sleep(4)

print("\n========== 成绩报告 ==========")
总对 = 总数 = 0
for 类, (对, 总) in 成绩.items():
    if 总:
        print(f"{类}类：{对}/{总}（{对/总*100:.0f}%）")
        总对 += 对; 总数 += 总
print(f"总正确率：{总对}/{总数}（{总对/总数*100:.0f}%）")
if 误答清单:
    print(f"\n⚠️ 误答警报（该拒答却答了，幻觉高危）：{len(误答清单)} 题")
    for 题 in 误答清单:
        print("   -", 题)
else:
    print("\n误答数：0 —— 危险指标零失分，漂亮。")
