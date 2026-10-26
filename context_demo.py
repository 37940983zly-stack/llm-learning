# ============================================
# 白板的理财学：压缩演示——10 轮老对话 vs 一段摘要
#
# 白板按 token 收租（每轮整份重发重计费）。老对话越积越贵。
# 压缩：让模型把老对话摘要成一段，用摘要替换原文——细节丢掉，要点保留。
#
# 跑法：python3 context_demo.py
# ============================================

import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

def 问模型(白板, 温度=0.3):
    卡片 = {"model": "glm-4.5-flash", "temperature": 温度, "messages": 白板}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(卡片).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            回应 = json.loads(resp.read())
        return 回应["choices"][0]["message"]["content"], 回应["usage"]["total_tokens"]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

# ---- 一段模拟的 10 轮咨询对话（每轮=user+assistant 两条）----
老对话 = [
    {"role": "user", "content": "我关注茅台、腾讯、宁德时代三只股票。"},
    {"role": "assistant", "content": "好的，已记下你的自选股：贵州茅台、腾讯控股、宁德时代。需要我每天收盘后帮你写复盘吗？"},
    {"role": "user", "content": "要的。我风格偏稳健，不追热点。"},
    {"role": "assistant", "content": "明白，复盘将按稳健风格写：重点提示风险，不推荐追高操作。"},
    {"role": "user", "content": "茅台我成本 1500 买的，10 股。"},
    {"role": "assistant", "content": "已记录：贵州茅台成本 1500 元/股 × 10 股。当前价 1650.5，浮盈约 10%。"},
    {"role": "user", "content": "宁德时代被套了，成本 210。"},
    {"role": "assistant", "content": "已记录：宁德时代成本 210 元/股。当前 188.7，浮亏约 10%。稳健策略建议：不急于补仓，观察 180 支撑位。"},
    {"role": "user", "content": "我每天只有晚上 9 点后有空看。"},
    {"role": "assistant", "content": "明白，复盘将固定在每晚 21:00 推送。"},
]

原文合计 = sum(len(m["content"]) for m in 老对话)
print(f"=== 压缩前：10 轮老对话，共 {len(老对话)} 条消息、约 {原文合计} 字 ===")
print("（这坨东西，每轮新对话都要整份塞上白板、整份重新计费）\n")

# ---- 压缩：让模型摘要 ----
摘要, 本次花费 = 问模型([
    {"role": "system", "content": "你是对话摘要员。把长对话压缩成要点清单，只保留对后续服务有用的事实，一条一行。"},
    {"role": "user", "content": "请摘要以下对话：\n" +
        "\n".join(f"{m['role']}: {m['content']}" for m in 老对话)},
])

print(f"=== 压缩后：摘要 {len(摘要)} 字（本次压缩花费 {本次花费} token，一次性）===\n")
print(摘要)
print(f"\n=== 账本对比 ===")
print(f"原文每轮重发约 {原文合计} 字 → 摘要版每轮只发约 {len(摘要)} 字，省约 {原文合计 // max(len(摘要),1)} 倍")
print("→ 压缩花一次钱，此后每一轮都在省——这就是白板的理财学。")
