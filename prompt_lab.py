# ============================================
# 提示词实验室第 1 弹：烂提示词 vs 骨架提示词
#
# 同一个需求（写今日复盘），两种说法，看回答差多少。
# 骨架五件套：角色 + 背景 + 任务 + 输入 + 格式（+ 限制）
#
# 跑法：python3 prompt_lab.py
# ============================================

import urllib.request, urllib.error, json, time

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(提示词):
    card = {
        "model": "glm-4.5-flash",
        "temperature": 0.7,
        "messages": [{"role": "user", "content": 提示词}],
    }
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            回应 = json.loads(resp.read())
        return 回应["choices"][0]["message"]["content"], 回应["usage"]["total_tokens"]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

行情 = """贵州茅台 1650.5 +2.5%（成交量放大）
腾讯控股 385.2 -1.2%
宁德时代 188.7 -3.1%（北向资金卖出）
中芯国际 78.4 +0.8%"""

烂提示词 = "帮我写个股票复盘"

骨架提示词 = f"""你是一位稳重的股票复盘助手，风格谨慎、不吹不黑。（角色）

我持仓关注 4 只股票，每天收盘后要看一份简短复盘。我不需要面面俱到，只要关键的。（背景）

请根据下面的行情数据，写今日复盘。（任务）

行情数据：
{行情}
（输入）

要求：每只股票一行，格式为"股票名｜涨跌｜一句话点评"；最后加一行"明日关注"。（格式）

总字数不超过 150 字；看不懂的走势就直说"看不懂"，不许编故事。（限制）"""

print("=" * 40)
print("【烂提示词】", 烂提示词)
print("-" * 40)
回答1, 花费1 = 问(烂提示词)
print(回答1)
print(f"（花费 {花费1} token）")

time.sleep(10)   # 歇口气，防 429

print()
print("=" * 40)
print("【骨架提示词】（五件套齐装，见程序源码）")
print("-" * 40)
回答2, 花费2 = 问(骨架提示词)
print(回答2)
print(f"（花费 {花费2} token）")

print()
print("=" * 40)
print(f"对比：烂版 {花费1} token | 骨架版 {花费2} token")
print("→ 回答质量差多少，自己读；token 差多少，自己看。")
