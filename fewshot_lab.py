# ============================================
# 提示词实验室第 2 弹：给例子 vs 光说不练 + 一步一步思考
#
# 实验 A：风格改写——Zero-shot（光提要求） vs Few-shot（给两个示范）
# 实验 B：算术题——不带咒语 vs 带"请一步一步思考"
#
# 跑法：python3 fewshot_lab.py（全程约 1 分钟，中间歇气防 429）
# ============================================

import urllib.request, urllib.error, json, time

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(提示词):
    card = {"model": "glm-4.5-flash", "temperature": 0.7,
            "messages": [{"role": "user", "content": 提示词}]}
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

# ---------- 实验 A：给例子 vs 光说不练 ----------
print("========== 实验 A：风格改写 ==========\n")

zero版 = "请把这句行情改写成老股民口吻的一句话点评，要带点江湖气：贵州茅台今日上涨2.5%，成交量放大。"

few版 = """请照着下面两个例子的风格，改写新行情。

例子1：
输入：宁德时代下跌3.1%，北向资金卖出
输出：宁王挨了一闷棍，外资撒腿跑，先别急着接飞刀。

例子2：
输入：中芯国际微涨0.8%
输出：中芯小碎步挪着走，不给力但也没趴下，继续观察。

现在改写：
输入：贵州茅台今日上涨2.5%，成交量放大
输出："""

print("--- 光说不练版（只有形容词要求）---")
print(问(zero版))

time.sleep(8)
print("\n--- 给例子版（两个示范先上白板）---")
print(问(few版))

time.sleep(8)
# ---------- 实验 B：一步一步思考 ----------
print("\n========== 实验 B：算术题 ==========\n")

题 = "我以每股1650元买了10股贵州茅台，后来跌了20%，又从低点涨了25%。请直接回答：我现在总市值是多少元？相比买入是赚了还是亏了？"

print("--- 不带咒语版 ---")
print(问(题))

time.sleep(8)
print("\n--- 带咒语版（请一步一步思考）---")
print(问(题 + "\n请一步一步思考：先算每个步骤，最后再给结论。"))

print("""
→ 看两处：①实验A里，哪版真正复刻了"宁王挨闷棍"那种味道？
          ②实验B里，两版答案各是多少？（正确答案：16500元，不赚不亏）
""")
