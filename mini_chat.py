# ============================================
# 迷你聊天程序：零件总装（项目① API Playground 核心骨架）
#
# 零件清单（全部是你学过的）：
#   咖啡机 = 问() 函数：投白板，掉出"回答+小票"
#   白板   = 白板 清单：问答历史
#   抄写员 = 白板.append(...)：每轮把双方的话抄上板
#   心脏   = while True 循环 + 判断出口（干到你说退出为止）
#   账本   = 总账 变量：小票一张张累加
#
# 跑法：python3 mini_chat.py
# 聊天：直接打字回车；退出：输入 q 或 退出
# ============================================

import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(白板):
    """咖啡机：投进去整块白板，掉出来两样——回答 + 小票（这次花了多少token）"""
    card = {"model": "glm-4.5-flash", "temperature": 0.7, "messages": 白板}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            回应 = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code)
        print("服务器的原话：", e.read().decode())
        print("（多半又是频率限制，等一分钟重跑即可，白板会重新开始）")
        return "【这一轮没接上，请再说一次】", 0
    小票 = 回应["usage"]["total_tokens"]           # 小票：这次调用花了多少 token
    return 回应["choices"][0]["message"]["content"], 小票

白板 = []      # 空白板，聊天历史从零开始
总账 = 0       # 账本：本次聊天累计花费

print("=== 迷你聊天程序 ===")
print("直接打字聊天。输入 q 退出。\n")

# ---- 程序的心脏：循环 + 判断出口 ----
while True:                                        # 【循环】一直转
    你说 = input("你：")                            # 程序的耳朵：等你打字
    if 你说 == "q" or 你说 == "退出":                # 【判断】唯一出口
        break
    if 你说 == "":                                  # 【判断】空手直接回车就重问
        continue

    白板.append({"role": "user", "content": 你说})          # 抄写员：抄你的话
    回答, 小票 = 问(白板)                                   # 按咖啡机：掉出回答+小票
    白板.append({"role": "assistant", "content": 回答})      # 抄写员：抄它的话
    总账 += 小票                                            # 账本累加

    print("AI：", 回答)
    print(f"（白板 {len(白板)} 条消息 | 累计 {总账} token）\n")

print(f"\n再见！本次聊天白板共 {len(白板)} 条消息，总消耗 {总账} token。")
