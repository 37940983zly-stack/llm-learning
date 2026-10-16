# ============================================
# 结构化输出：让模型必须按 JSON 卡片回话
#
# 为什么：程序读不懂自然语言（"今天涨了2.5%呢"没法自动处理），
#        但程序读得懂格式固定的 JSON 卡片。
# 做法：① 请求里 response_format 声明"只回 JSON"
#      ② 提示词里给出卡片模板
#      （若报 4xx 错误：删掉 response_format 那行再跑，靠提示词约定也基本管用）
#
# 跑法：python3 structured_demo.py
# ============================================

import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(白板):
    card = {
        "model": "glm-4.5-flash",
        "temperature": 0.1,                              # 提取信息：低温，要稳（对照第10课的表）
        "messages": 白板,
        "response_format": {"type": "json_object"},      # ★ 跟服务器约定：只回 JSON
    }
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            回应 = json.loads(resp.read())
        return 回应["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

新闻 = "贵州茅台今日收盘上涨2.5%，成交量明显放大，北向资金净买入约3亿元。"

格式约定 = '{"股票名": "", "方向": "涨/跌/平三选一", "变动幅度": "", "一句话摘要": ""}'

白板 = [{
    "role": "user",
    "content": "从下面的新闻里提取信息。只输出一个 JSON，格式严格照抄这个模板填空：" + 格式约定 + "。新闻原文：" + 新闻
}]

raw = 问(白板)
print("模型的原始回答（一串像卡片的文字）：")
print(raw)

卡片 = json.loads(raw)      # ★ 程序拆包：因为格式是约定死的，这里一定能拆开

print("\n程序读到了——")
print("股票名　：", 卡片["股票名"])
print("方向　　：", 卡片["方向"])
print("变动幅度：", 卡片["变动幅度"])
print("摘要　　：", 卡片["一句话摘要"])

print("\n→ 接下来程序就能自动干活了，比如：")
if 卡片["方向"] == "涨":
    print("   检测到方向=涨 → 自动在复盘日志里记一笔【看多观察】（这就是 fupan.py 的全自动版雏形！）")
