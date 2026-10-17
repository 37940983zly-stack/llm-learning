# ============================================
# 多轮对话实验：亲手当"抄写员"
#
# 揭开真相：所谓"它记得上文"，
# 就是程序把双方说过的话一条条抄回白板，每次整份重发。
# 跑法：python3 chat.py
# ============================================

import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(白板):
    card = {"model": "glm-4.5-flash", "temperature": 0.7, "messages": 白板}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code)
        print("服务器的原话：", e.read().decode())
        raise SystemExit

# 白板从一张空清单开始
白板 = []

# ---- 第一轮：我说一句，它答一句 ----
白板.append({"role": "user", "content": "记住一个秘密：我最喜欢的股票是贵州茅台。用一句话回应我。"})
回答1 = 问(白板)
print("第一轮它的回答：", 回答1)

# 关键一步：把它的回答抄上白板（聊天工具背后每天在干的事）
白板.append({"role": "assistant", "content": 回答1})

# ---- 第二轮：问一个"只有看白板才知道答案"的问题 ----
白板.append({"role": "user", "content": "刚才说我最喜欢的股票是哪只？只答股票名。"})
回答2 = 问(白板)
print("第二轮它的回答：", 回答2)

# ---- 展示此刻的白板 ----
print("\n此刻白板上共", len(白板), "条消息：")
for 消息 in 白板:
    print(" -", 消息["role"], "说：", 消息["content"][:30])
