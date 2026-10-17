# ============================================
# 双模型对比台：同一问题，问两个模型，并排打分
#
# 原文项目①验收要求："对比两个模型/供应商；记录 Token 用量和耗时"
# 对比的三个维度：速度（耗时）、花费（token）、回答风格
#
# 新零件：秒表（time）——出发前看一次表，到达后看一次表，相减=耗时
#
# 跑法：python3 compare.py
# ============================================

import urllib.request, urllib.error, json, time

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(选手, 问题):
    """同一个咖啡机，换个豆子（模型名）"""
    card = {
        "model": 选手,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": 问题}],
    }
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    出发 = time.time()                                  # 出发前看表
    try:
        with urllib.request.urlopen(req) as resp:
            回应 = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit
    到达 = time.time()                                  # 到达后看表
    回答 = 回应["choices"][0]["message"]["content"]
    小票 = 回应["usage"]
    return 回答, 到达 - 出发, 小票

问题 = "用三句话向完全不懂股票的人解释：什么是'追涨杀跌'，为什么它容易亏钱？"

选手们 = [
    "glm-4.5-flash",        # 免费档选手一
    "glm-4-flash-250414",   # 免费档选手二（若报模型不存在，换成 "glm-4-flash" 再跑）
]

成绩单 = {}   # 仓库：每个选手的成绩存这里，最后小结用

for 选手 in 选手们:                        # 清单式循环：对每个选手来一遍（第3课股票清单同款）
    print(f"--- 正在问 {选手} ---")
    回答, 耗时, 小票 = 问(选手, 问题)
    成绩单[选手] = (回答, 耗时, 小票)
    print(回答)
    print(f"（耗时 {耗时:.1f} 秒 | prompt {小票['prompt_tokens']} + completion {小票['completion_tokens']} = {小票['total_tokens']} token）\n")
    if 选手 != 选手们[-1]:
        print("（歇 10 秒，给免费档门卫留个面子……）")
        time.sleep(10)

print("=== 对比小结 ===")
for 选手, (回答, 耗时, 小票) in 成绩单.items():
    print(f"{选手}：{耗时:.1f} 秒 | {小票['total_tokens']} token | 回答 {len(回答)} 字")
print("\n→ 三个维度看完，你会为'每日自动复盘'这个任务选谁？")
