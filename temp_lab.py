# ============================================
# 温度实验：同一个问题，两种性格
#
# 跑法：python3 temp_lab.py
# 建议连跑两三遍，对比"低温的输出变不变、高温的输出变不变"
# ============================================

import urllib.request   # 寄包裹工具
import urllib.error     # 接住服务器拒绝
import json             # 打包/拆包

with open("key.txt") as f:
    my_key = f.read().strip()

# 问() 就是一台咖啡机：投进去"问题+温度"，掉出来"回答"
# （第 2 课的哲学落地：换豆子（温度）不动机器）
def 问(问题, 温度):
    card = {
        "model": "glm-4.5-flash",
        "temperature": 温度,                # 任性旋钮在这里转
        "messages": [{"role": "user", "content": 问题}]
    }
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

问题 = "用一个比喻形容'学习编程'这件事"

print("=== 低温 0.1（一板一眼的会计）===")
print(问(问题, 0.1))

print()
print("=== 高温 0.95（放飞自我的段子手）===")
print(问(问题, 0.95))
