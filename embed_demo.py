# ============================================
# Embedding：给句子做"含义指纹"
#
# 把一句话变成一串数字（向量）。含义相近的句子，
# 指纹也相近——程序由此会"比含义"，而不只是比字面。
#
# 这是未来 RAG（让 AI 查完资料再回答）的地基：
# 把你的资料全部做成指纹存进"含义地图"，新问题也做成指纹，
# 地图上离得最近的几段资料，就是最相关的资料。
#
# 跑法：python3 embed_demo.py
# 若报"模型不存在"：把 embedding-3 换成 embedding-2 再跑
# ============================================

import urllib.request, urllib.error, json, math

with open("key.txt") as f:
    my_key = f.read().strip()

def 做指纹(句子们):
    """一次批量做：投进去一叠句子，掉出来一叠指纹"""
    card = {"model": "embedding-3", "input": 句子们}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/embeddings",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            回应 = json.loads(resp.read())
        return [d["embedding"] for d in 回应["data"]]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

def 相似度(a, b):
    """两串指纹的"含义距离分数"：越接近 1 越像，越接近 0 越不像（数学不用管，当尺子用）"""
    点积 = sum(x * y for x, y in zip(a, b))
    长a = math.sqrt(sum(x * x for x in a))
    长b = math.sqrt(sum(y * y for y in b))
    return 点积 / (长a * 长b)

句子们 = [
    "我今天心情很好",
    "今日心情愉快",
    "股价大跌，市值蒸发",
]

指纹们 = 做指纹(句子们)

print("=== 每句话的指纹（一串数字，只看前 5 个）===")
for 句, 指纹 in zip(句子们, 指纹们):
    print(f"『{句}』→ {len(指纹)} 个数字，前5个：{[round(x, 3) for x in 指纹[:5]]}")

print("\n=== 两两之间的含义相似度 ===")
print(f"『{句子们[0]}』vs『{句子们[1]}』：{相似度(指纹们[0], 指纹们[1]):.3f}   ← 字面不同，含义近")
print(f"『{句子们[0]}』vs『{句子们[2]}』：{相似度(指纹们[0], 指纹们[2]):.3f}   ← 含义远")
print(f"『{句子们[1]}』vs『{句子们[2]}』：{相似度(指纹们[1], 指纹们[2]):.3f}")
