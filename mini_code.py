# ============================================
# 项目③：迷你 Coding Agent（mini_code.py）
#
# 一个能真正干活的 Harness：
#   四个按钮：读文件 / 写文件 / 列目录 / 跑命令
#   一个 Loop：看→想→做→记（预算 8 轮）
#   一道防线：写文件、跑命令前——打印预览，人点头才执行（第6课学以致用）
#
# 跑法：python3 mini_code.py
# 首跑任务：读取 fupan.py，总结它的功能，把总结写进 说明书.txt
# ============================================

import urllib.request, urllib.error, json, os, subprocess

with open("key.txt") as f:
    my_key = f.read().strip()

def 问模型(白板, 工具):
    卡片 = {"model": "glm-4.5-flash", "temperature": 0.2,
            "messages": 白板, "tools": 工具}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(卡片).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

# ===== 四个真按钮 =====
def 读文件(路径):
    try:
        with open(路径) as f:
            内容 = f.read()
        return 内容[:2000] + ("\n…（太长已截断）" if len(内容) > 2000 else "")
    except Exception as e:
        return f"读失败：{e}"

def 写文件(路径, 内容):
    print(f"\n  ⚠️ 即将写文件：{路径}")
    print("  预览（前 200 字）：", 内容[:200].replace("\n", " "))
    if input("  允许写入？(y/n)：").strip().lower() != "y":     # 人审：不可逆动作先问
        return "用户拒绝了写入。"
    with open(路径, "w") as f:
        f.write(内容)
    return f"已写入 {路径}（{len(内容)} 字）"

def 列目录(路径="."):
    try:
        return "\n".join(sorted(os.listdir(路径))[:50])
    except Exception as e:
        return f"列目录失败：{e}"

def 跑命令(命令):
    print(f"\n  ⚠️ 即将执行命令：{命令}")
    if input("  允许执行？(y/n)：").strip().lower() != "y":     # 人审：最危险的按钮
        return "用户拒绝了执行。"
    try:
        结果 = subprocess.run(命令, shell=True, capture_output=True, text=True, timeout=20)
        输出 = (结果.stdout + 结果.stderr)[:1500]
        return 输出 or f"（无输出，返回码 {结果.returncode}）"
    except Exception as e:
        return f"命令失败：{e}"

按钮说明书 = [
    {"type": "function", "function": {
        "name": "读文件",
        "description": "读取一个文本文件的内容。需要了解某个文件时用它。",
        "parameters": {"type": "object",
                       "properties": {"路径": {"type": "string", "description": "文件路径"}},
                       "required": ["路径"]}}},
    {"type": "function", "function": {
        "name": "写文件",
        "description": "把内容写入文件（覆盖式）。需要创建或修改文件时用它。",
        "parameters": {"type": "object",
                       "properties": {"路径": {"type": "string"},
                                      "内容": {"type": "string", "description": "要写入的完整内容"}},
                       "required": ["路径", "内容"]}}},
    {"type": "function", "function": {
        "name": "列目录",
        "description": "列出文件夹里有哪些文件。需要查看工作目录内容时用它。",
        "parameters": {"type": "object",
                       "properties": {"路径": {"type": "string", "description": "文件夹路径，默认当前目录"}},
                       "required": []}}},
    {"type": "function", "function": {
        "name": "跑命令",
        "description": "执行一条终端命令并返回输出。需要运行程序、查看系统信息时用它。谨慎使用。",
        "parameters": {"type": "object",
                       "properties": {"命令": {"type": "string"}},
                       "required": ["命令"]}}},
]
真按钮 = {"读文件": 读文件, "写文件": 写文件, "列目录": 列目录, "跑命令": 跑命令}

# ===== Agent Loop =====
print("=== 迷你 Coding Agent（输入 q 退出）===")
print("四个按钮：读文件 / 写文件 / 列目录 / 跑命令（后两个需要你点头）\n")

while True:
    任务 = input("任务：")
    if 任务 in ("q", "quit", "退出"):
        break
    if 任务 == "":
        continue

    白板 = [
        {"role": "system", "content":
            "你是一个文件助理 Agent，在一个学习项目文件夹里工作。"
            "用提供的按钮完成任务；文件操作优先用按钮而不是猜。"
            "任务完成后，直接用文字汇报结果，不再按任何按钮。"},
        {"role": "user", "content": 任务},
    ]

    for 轮次 in range(1, 9):                          # 预算：最多 8 轮
        消息 = 问模型(白板, 按钮说明书)
        if not 消息.get("tool_calls"):                  # 不再喊按钮 = 自认完成
            print(f"\n🏁 完成（第 {轮次} 轮）：{消息['content']}\n")
            break
        白板.append(消息)
        for 喊话 in 消息["tool_calls"]:
            按钮名 = 喊话["function"]["name"]
            参数 = json.loads(喊话["function"]["arguments"])
            参数摘要 = str(参数)[:80]
            print(f"  [第{轮次}轮] 模型按下：{按钮名}({参数摘要})")
            结果 = 真按钮[按钮名](**参数)
            白板.append({"role": "tool", "tool_call_id": 喊话["id"], "content": 结果})
    else:
        print("\n⏸ 预算用尽（8 轮），强制停止。\n")

print("再见。")
