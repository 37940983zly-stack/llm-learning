# ============================================
# 迷你聊天 2.0：流式版——回答逐字蹦出来
#
# 和 mini_chat.py 唯一的本质区别：
#   请求卡片里加了 "stream": true
#   响应从"一个大包裹"变成"一连串小包裹"，收到一件打印一件
#
# 跑法：python3 stream_chat.py   （体验和 mini_chat 对比！）
# ============================================

import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

def 问流式(白板):
    """流式咖啡机：字一到就打印；最后掉出（完整回答, 小票）"""
    card = {
        "model": "glm-4.5-flash",
        "temperature": 0.7,
        "messages": 白板,
        "stream": True,                      # ★ 关键开关：边接边寄
    }
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    完整回答 = ""
    小票 = 0
    print("AI：", end="",flush=True)         # 先报幕，字随后一个个来
    try:
        with urllib.request.urlopen(req) as resp:
            for 行 in resp:                   # 服务器一件一件寄，我们一件一件收
                行 = 行.decode().strip()
                if not 行.startswith("data:"):
                    continue                  # 不是货的行（空行等）跳过
                货 = 行[5:].strip()           # 剥掉 "data: " 外皮
                if 货 == "[DONE]":            # "寄完了"的暗号
                    break
                小包裹 = json.loads(货)
                新字 = 小包裹["choices"][0]["delta"].get("content", "")   # delta=这一件里的增量
                print(新字, end="", flush=True)   # end=""：打完不换行，字才连得成句
                完整回答 += 新字
                if 小包裹.get("usage"):       # 小票有时塞在最后一包里
                    小票 = 小包裹["usage"].get("total_tokens", 0)
    except urllib.error.HTTPError as e:
        print("\n服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        print("（多半又是频率限制，等一分钟重跑）")
    print()                                   # 回答收尾，换行
    return 完整回答, 小票

白板 = []
总账 = 0

print("=== 迷你聊天 2.0（流式版）===")
print("回答会逐字蹦出来。输入 q 退出。\n")

while True:
    你说 = input("你：")
    if 你说 in ("q", "退出"):
        break
    if 你说 == "":
        continue
    白板.append({"role": "user", "content": 你说})
    回答, 小票 = 问流式(白板)
    白板.append({"role": "assistant", "content": 回答})
    总账 += 小票
    print(f"（白板 {len(白板)} 条 | 累计 {总账} token）\n")

print(f"\n再见！白板共 {len(白板)} 条，总消耗 {总账} token。")
