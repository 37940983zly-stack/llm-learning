# ============================================
# 项目② 第一块砖：最小 RAG——翻着你的书回答你的问题
#
# 备菜（启动时一次）：舆情清单 → 一条一块（纯橙汁）→ 批量做指纹 → 知识库
# 答题（每问一次）：问题做指纹 → 找 Top-2 → 过拒答线检查 → 带引用上白板 → 模型作答
#
# 跑法：python3 rag_mini.py
# 试试三问：①穿山甲相关的舆情有哪些？②抖音上发生了什么？③比特币今天行情如何？
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

def 问模型(白板):
    card = {"model": "glm-4.5-flash", "temperature": 0.3, "messages": 白板}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        return "【调用失败】"

# ============ 备菜阶段：启动时做一次 ============
舆情清单 = [
    "1.【微博】10月15日，网友举报某直播间疑似售卖穿山甲鳞片制品，涉案账号已被平台封禁。",
    "2.【抖音】10月16日，一段深山捕兽夹视频热传，警方已介入调查。",
    "3.【贴吧】10月14日，有人发帖询问哪里能买到象牙手串，被网友集体举报。",
    "4.【公众号】10月17日，某文章科普野生动物保护法修订要点，阅读量十万加。",
    "5.【微博】10月18日，海关通报查获走私穿山甲鳞片20公斤，3人被刑事拘留。",
    "6.【小红书】10月16日，用户晒出野生兰花照片被专家指出是保护植物，已删除。",
    "7.【抖音】10月19日，主播食用野生娃娃鱼被查处，实为人工养殖，误导宣传被处罚。",
]

print("备菜中：切块 → 做指纹 → 建知识库……")
知识库指纹们 = 做指纹(舆情清单)      # 一条一块，批量做指纹
print(f"知识库就绪：{len(舆情清单)} 块。\n")

拒答线 = 0.50   # 最高相似度低于这条线 → 资料里八成没有 → 不调模型直接拒答
                 # （这条线该定多高，等你问完三个测试题自己决定——见课后任务）

print("=== 最小 RAG 已启动（输入 q 退出）===")
print("建议依次问：①穿山甲相关的舆情有哪些？②抖音上发生了什么？③比特币今天行情如何？\n")

# ============ 答题阶段：每问一次 ============
while True:
    问题 = input("你问：")
    if 问题 in ("q", "quit", "退出"):
        break
    if 问题 == "":
        continue

    问题指纹 = 做指纹([问题])[0]                       # 问题：一句 → 一个指纹（不切！）
    排名 = sorted(range(len(舆情清单)),
                  key=lambda i: -相似度(问题指纹, 知识库指纹们[i]))
    最高分 = 相似度(问题指纹, 知识库指纹们[排名[0]])

    # —— 第一步亮牌：检索到了什么 ——
    print(f"\n[检索] Top-2：")
    for 名次, 索引 in enumerate(排名[:2]):
        print(f"  [{名次+1}] 相似度 {相似度(问题指纹, 知识库指纹们[索引]):.3f} → {舆情清单[索引][:40]}……")

    # —— 第二步：拒答线检查（不编的保险丝） ——
    if 最高分 < 拒答线:
        print(f"[拒答] 最高分 {最高分:.3f} 低于拒答线 {拒答线}：知识库里没有相关资料，不编。")
        continue

    # —— 第三步：组白板（导演批示 + 带编号的资料 + 问题） ——
    白板 = [
        {"role": "system", "content":
            "你是舆情分析助手。只能根据【参考资料】回答问题，回答末尾用 [编号] 标注引用了哪条资料；"
            "资料里没有的信息，就明说'资料中未提及'，绝不编造。"},
        {"role": "user", "content":
            "参考资料：\n[1] " + 舆情清单[排名[0]] + "\n[2] " + 舆情清单[排名[1]] +
            "\n\n问题：" + 问题},
    ]

    # —— 第四步：模型看着资料作答 ——
    回答 = 问模型(白板)
    print(f"\nAI：{回答}\n")

print("再见。")
