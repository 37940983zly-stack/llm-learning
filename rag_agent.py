# ============================================
# 项目② 完全体：RAG + Tool Calling Agent
#
# 两个按钮，模型自己挑：
#   [查舆情知识库] —— rag_v2 的检索（粗排+拒答线+精排）打包成一个按钮
#   [查股价]       —— 模块一的老按钮
# 知识库外部化：资料从 知识库.txt 读取（不再写死在程序里）
#
# 用法：
#   1. 先在同目录建 知识库.txt（一行一条舆情，程序会读它建库）
#   2. python3 rag_agent.py
#   3. 试试：①穿山甲舆情有哪些？②贵州茅台多少钱？③帮我写首关于秋天的诗
# ============================================

import urllib.request, urllib.error, json, math, os

with open("key.txt") as f:
    my_key = f.read().strip()

def 调接口(地址, 卡片):
    req = urllib.request.Request(
        地址, data=json.dumps(卡片).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
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
    回应 = 调接口("https://open.bigmodel.cn/api/paas/v4/chat/completions", 卡片)
    return 回应["choices"][0]["message"]

# ====== 备菜：知识库外部化——从文件读资料 ======
if not os.path.exists("知识库.txt"):
    with open("知识库.txt", "w") as f:
        f.write("网友举报某直播间疑似售卖穿山甲鳞片制品，涉案账号已被平台封禁。\n"
                "一段深山捕兽夹视频热传，警方已介入调查。\n"
                "有人发帖询问哪里能买到象牙手串，被网友集体举报。\n"
                "某文章科普野生动物保护法修订要点，阅读量十万加。\n"
                "海关通报查获走私穿山甲鳞片20公斤，3人被刑事拘留。\n"
                "用户晒出野生兰花照片被专家指出是保护植物，已删除。\n"
                "主播食用野生娃娃鱼被查处，实为人工养殖，误导宣传被处罚。\n")
    print("（未找到知识库.txt，已自动生成一份示例——以后你可随时编辑它，重启程序生效）")

with open("知识库.txt") as f:
    知识库 = [行.strip() for 行 in f if 行.strip()]
知识库指纹们 = 做指纹(知识库)
print(f"知识库就绪：从 知识库.txt 读入 {len(知识库)} 条。\n")

拒答线 = 0.40    # 你调出来的那条线

# ====== 按钮 1：查舆情知识库（rag_v2 的检索打包成一个函数）======
def 查舆情知识库(问题):
    问题指纹 = 做指纹([问题])[0]
    排名 = sorted(range(len(知识库)), key=lambda i: -相似度(问题指纹, 知识库指纹们[i]))
    最高分 = 相似度(问题指纹, 知识库指纹们[排名[0]])
    if 最高分 < 拒答线:
        return "知识库中无相关资料。"                     # 按钮如实回报，模型自己决定怎么说
    候选 = [知识库[i] for i in 排名[:5]]
    编号清单 = "".join(f"[{i+1}] {条}\n" for i, 条 in enumerate(候选))
    精排白板 = [
        {"role": "system", "content": "你是检索质量审核员，只输出 JSON。"},
        {"role": "user", "content": "候选资料：\n" + 编号清单 +
            "问题：" + 问题 + '\n挑出最能回答问题的2条，只输出 {"选择":[编号,编号]}'},
    ]
    选择 = json.loads(问模型(精排白板, 温度=0.1)["content"])["选择"]
    精选 = [候选[i - 1] for i in 选择 if 0 < i <= len(候选)][:2]
    return "检索结果：\n" + "".join(f"[{i+1}] {条}\n" for i, 条 in enumerate(精选))

# ====== 按钮 2：查股价（模块一的老朋友）======
def 查股价(股票名):
    行情 = {"贵州茅台": 1650.5, "腾讯控股": 385.2, "宁德时代": 188.7}
    if 股票名 in 行情:
        return f"{股票名} 当前价格 {行情[股票名]} 元"    # 按钮结果必须是文字，裸数字会被服务器拒收
    return f"没有 {股票名} 的数据（可查：贵州茅台/腾讯控股/宁德时代）"

# ====== 按钮说明书（模型只能从这份清单里挑）======
按钮说明书 = [
    {"type": "function", "function": {
        "name": "查舆情知识库",
        "description": "查询野生动植物网络违法舆情知识库。涉及舆情、举报、违法案件、保护动物的问题用它。",
        "parameters": {"type": "object",
                       "properties": {"问题": {"type": "string", "description": "要检索的问题"}},
                       "required": ["问题"]}}},
    {"type": "function", "function": {
        "name": "查股价",
        "description": "查询股票当前价格。问某只股票多少钱时用它。可查：贵州茅台、腾讯控股、宁德时代。",
        "parameters": {"type": "object",
                       "properties": {"股票名": {"type": "string", "description": "股票中文名"}},
                       "required": ["股票名"]}}},
]

真按钮 = {"查舆情知识库": 查舆情知识库, "查股价": 查股价}

print("=== RAG + Tool Calling Agent（q 退出）===")
print("试试：①穿山甲舆情有哪些？ ②贵州茅台多少钱？ ③帮我写首关于秋天的诗\n")

while True:
    你说 = input("你：")
    if 你说 in ("q", "quit", "退出"):
        break
    if 你说 == "":
        continue

    白板 = [
        {"role": "system", "content":
            "你是助手，身边有两个按钮（见工具清单）。该查资料/查股价就按按钮；"
            "与两者都无关的问题就直接回答，不要硬按。"},
        {"role": "user", "content": 你说},
    ]

    for 轮次 in range(3):                    # 最多按三轮按钮，防失控
        消息 = 问模型(白板, 工具=按钮说明书)
        if not 消息.get("tool_calls"):
            print("AI：", 消息["content"])
            break
        白板.append(消息)                    # 模型的喊话抄上白板
        for 喊话 in 消息["tool_calls"]:
            按钮名 = 喊话["function"]["name"]
            参数 = json.loads(喊话["function"]["arguments"])
            print(f"  [模型按下按钮] {按钮名}({参数})")
            结果 = 真按钮[按钮名](**参数)     # 程序真正执行
            白板.append({"role": "tool", "tool_call_id": 喊话["id"], "content": 结果})
    else:
        print("AI：（按钮按太多次了，停一下）")

print("再见。")
