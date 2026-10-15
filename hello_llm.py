# ============================================
# 第一次亲手调用大模型（项目① API Playground 第一块砖）
#
# 用到的全是学过的：HTTP 寄包裹（POST）、JSON 打包（卡片/清单）、
# 白板规矩（messages）、门票（API Key，代码和密钥分家）
#
# v2：加了两件新装备——
#   ① 温度（temperature）：接龙的"任性旋钮"
#   ② 报错翻译器：服务器拒绝时，把它的原话说给你听
#
# 如果报错说模型不存在：把下面 "glm-4.7-flash" 换成 "glm-4.5-flash" 再跑
# ============================================

import urllib.request   # Python 自带的寄包裹工具（不用安装任何东西）
import urllib.error     # 专门接住"服务器拒绝"的工具
import json             # JSON 打包/拆包工具

# 1) 读门票：key 单独放在 key.txt 里——绝不写进代码、绝不进 GitHub
with open("key.txt") as f:
    my_key = f.read().strip()

# 2) 组白板：寄给模型的货，是一张 JSON 卡片
card = {
    "model": "glm-4.5-flash",            # 用哪个模型（免费档）
    "temperature": 0.8,                   # 任性旋钮：1.0 左右活泼，0.1 一板一眼（0~1 之间）
    "messages": [                         # 白板：一段对话清单（[] 是清单！）
        {"role": "user", "content": "用一句话向纯小白介绍你自己，并说说你的知识截止到什么时候"}
    ]
}

# 3) 寄包裹：POST 到智谱的地址，门票贴在快递单上（headers）
req = urllib.request.Request(
    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    data=json.dumps(card).encode(),       # 卡片打包成 JSON 文本再寄出
    headers={
        "Content-Type": "application/json",     # 快递单注明：里面是 JSON
        "Authorization": "Bearer " + my_key,    # 门票贴在这里
    },
)

# 4) 收包裹、拆包（报错翻译器装在这里：被拒时听服务器把话说完）
try:
    with urllib.request.urlopen(req) as resp:
        reply = json.loads(resp.read())   # 拆出来又是一张 JSON 大卡片
except urllib.error.HTTPError as e:
    print("服务器拒绝了，状态码：", e.code)
    print("服务器的原话：", e.read().decode())   # 把服务器的解释读出来
    raise SystemExit                     # 优雅退出，不甩一大屏红字

# 5) 读卡片：回答藏在 choices[0] -> message -> content 这条路径上
print("=== 模型的回答 ===")
print(reply["choices"][0]["message"]["content"])

# 6) 看计价器：这次白板写了多少（prompt）、它接了多少（completion）
print("\n=== 计价器（usage）===")
print(reply["usage"])
