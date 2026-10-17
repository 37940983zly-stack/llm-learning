# ============================================
# 工具调用（Function Calling）：教 AI 按按钮
#
# 三幕剧：
#   第一幕：模型没有现成答案，"喊"：请按『查股价』按钮，投进"贵州茅台"
#   第二幕：程序真的按按钮（执行真函数），拿到结果
#   第三幕：结果抄回白板，再问一次模型，它说出最终答案
#
# 铁律不变：模型看得见白板、写不了白板——它只负责"喊"，
#          按钮永远在程序手里。
#
# 跑法：python3 tool_demo.py
# ============================================

import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

def 调模型(白板, 带工具=False):
    card = {"model": "glm-4.5-flash", "temperature": 0.1, "messages": 白板}
    if 带工具:
        card["tools"] = [{                        # 告诉模型：你身边有这些按钮
            "type": "function",
            "function": {
                "name": "查股价",
                "description": "查询一只股票的当前价格。可查：贵州茅台、腾讯控股、宁德时代。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "股票名": {"type": "string", "description": "股票的中文名"}
                    },
                    "required": ["股票名"],
                },
            },
        }]
    req = urllib.request.Request(
        URL, data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

# ---- 真按钮：程序里的真函数（这里是模拟数据源，以后可换成真行情接口）----
def 查股价(股票名):
    行情 = {"贵州茅台": 1650.5, "腾讯控股": 385.2, "宁德时代": 188.7}
    return f"{股票名} 当前价格 {行情[股票名]} 元"

白板 = [{"role": "user", "content": "贵州茅台现在多少钱一股？"}]

# ---- 第一幕：模型喊按钮 ----
回应 = 调模型(白板, 带工具=True)
消息 = 回应["choices"][0]["message"]

if 消息.get("tool_calls"):
    喊话 = 消息["tool_calls"][0]
    按钮名 = 喊话["function"]["name"]
    参数 = json.loads(喊话["function"]["arguments"])     # 模型投的东西（一段 JSON 文本，拆开）
    print(f"【第一幕】模型没有现成答案（它的知识有保质期），它喊：")
    print(f"          请按『{按钮名}』按钮，投进去：{参数}")
    白板.append(消息)                                     # 把模型的喊话原样抄上白板

    # ---- 第二幕：程序按按钮（真正干活的时刻）----
    结果 = 查股价(**参数)                                  # **参数 = 把卡片里的键值当参数投进去
    print(f"【第二幕】程序真的按了按钮，拿到结果：{结果}")
    白板.append({"role": "tool", "tool_call_id": 喊话["id"], "content": 结果})  # 结果抄回白板，对上号

    # ---- 第三幕：模型看着白板上的结果，说出人话 ----
    回应2 = 调模型(白板)
    print(f"【第三幕】模型看着白板上的结果，回答：{回应2['choices'][0]['message']['content']}")
else:
    print("模型没喊按钮，直接答了：", 消息["content"])
    print("（再跑一次试试；模型偶尔会忘了按钮存在）")
