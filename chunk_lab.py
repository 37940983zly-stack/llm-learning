# ============================================
# 分块实验室：切菜刀法对比——固定切 vs 按条目切
#
# 同一份《舆情简报》（7 条），两种切法：
#   A 固定长度切：每 40 个字一刀，不管句子死活
#   B 按条目切：顺着天然关节（每行一条）切
# 然后同一个问题（"穿山甲走私的舆情有哪些？"），
# 两种切法各自找最相近的 2 块——看谁找得准。
#
# 跑法：python3 chunk_lab.py
# ============================================

import urllib.request, urllib.error, json, math

with open("key.txt") as f:
    my_key = f.read().strip()

def 做指纹(句子们):
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
    点积 = sum(x * y for x, y in zip(a, b))
    长a = math.sqrt(sum(x * x for x in a))
    长b = math.sqrt(sum(y * y for y in b))
    return 点积 / (长a * 长b)

简报 = """1.【微博】10月15日，网友举报某直播间疑似售卖穿山甲鳞片制品，涉案账号已被平台封禁。
2.【抖音】10月16日，一段深山捕兽夹视频热传，警方已介入调查。
3.【贴吧】10月14日，有人发帖询问哪里能买到象牙手串，被网友集体举报。
4.【公众号】10月17日，某文章科普野生动物保护法修订要点，阅读量十万加。
5.【微博】10月18日，海关通报查获走私穿山甲鳞片20公斤，3人被刑事拘留。
6.【小红书】10月16日，用户晒出野生兰花照片被专家指出是保护植物，已删除。
7.【抖音】10月19日，主播食用野生娃娃鱼被查处，实为人工养殖，误导宣传被处罚。"""

# ---- 切法 A：固定长度，每 40 字一刀，不管句子死活 ----
固定块们 = []
for 起点 in range(0, len(简报), 40):
    固定块们.append(简报[起点:起点 + 40])

# ---- 切法 B：按条目切（顺着天然关节：每行一条）----
条目块们 = [行 for 行 in 简报.split("\n") if 行.strip()]

print(f"=== 切法 A：固定 40 字一刀，共 {len(固定块们)} 块 ===")
for i, 块 in enumerate(固定块们[:4]):
    print(f"块{i+1}：{块}")
print("……（看到拦腰斩了吗？句子被切断的地方）\n")

print(f"=== 切法 B：按条目切，共 {len(条目块们)} 块 ===")
for i, 块 in enumerate(条目块们[:3]):
    print(f"块{i+1}：{块[:30]}……")
print("……（每条舆情完整一块）\n")

# ---- 同一个问题，两种切法各自找 Top-2 ----
问题 = "穿山甲走私的舆情有哪些？"
问题指纹 = 做指纹([问题])[0]

def 找最近(块们, 标签):
    指纹们 = 做指纹(块们)
    排名 = sorted(range(len(块们)), key=lambda i: -相似度(问题指纹, 指纹们[i]))
    print(f"=== {标签} 找到的最相近 2 块 ===")
    for 名次 in 排名[:2]:
        得分 = 相似度(问题指纹, 指纹们[名次])
        print(f"Top{排名.index(名次)+1}（相似度 {得分:.3f}）：{块们[名次]}")
    print()

找最近(固定块们, "切法 A（固定切）")
找最近(条目块们, "切法 B（条目切）")

print("→ 对比：哪种切法找到的块，语义是完整的？")
