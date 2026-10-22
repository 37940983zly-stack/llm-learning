# ============================================
# 项目② 第二块砖：RAG 2.0——粗排+精排+元数据过滤
#
# 相比 rag_mini 的三处升级：
#   ① 条目带元数据（平台/日期标签）
#   ② 粗排扩池：Top-5 进候选（原来是 Top-2 直接用）
#   ③ LLM 当精排员：从 5 个候选里挑真正最相关的 2 个（结构化输出回编号）
#
# 招聘类比：粗排=HR 扫简历（快而糙，从全员筛出候选池）
#          精排=主管面试（贵而准，从候选池选出真命天子）
# ============================================

import urllib.request, urllib.error, json, math

with open("key.txt") as f:
    my_key = f.read().strip()

def 调接口(地址, 卡片):
    req = urllib.request.Request(
        地址, data=json.dumps(卡片).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("服务器拒绝了，状态码：", e.code, "原话：", e.read().decode())
        raise SystemExit

def 做指纹(句子们):
    return [d["embedding"] for d in
            调接口("https://open.bigmodel.cn/api/paas/v4/embeddings",
                    {"model": "embedding-3", "input": 句子们})["data"]]

def 相似度(a, b):
    点积 = sum(x * y for x, y in zip(a, b))
    长a = math.sqrt(sum(x * x for x in a))
    长b = math.sqrt(sum(y * y for y in b))
    return 点积 / (长a * 长b)

def 问模型(白板, 温度=0.3):
    回应 = 调接口("https://open.bigmodel.cn/api/paas/v4/chat/completions",
                   {"model": "glm-4.5-flash", "temperature": 温度, "messages": 白板})
    return 回应["choices"][0]["message"]["content"]

# ====== 备菜：条目带元数据（平台/日期标签）======
知识库 = [
    {"平台": "微博",  "日期": "10-15", "内容": "网友举报某直播间疑似售卖穿山甲鳞片制品，涉案账号已被平台封禁。"},
    {"平台": "抖音",  "日期": "10-16", "内容": "一段深山捕兽夹视频热传，警方已介入调查。"},
    {"平台": "贴吧",  "日期": "10-14", "内容": "有人发帖询问哪里能买到象牙手串，被网友集体举报。"},
    {"平台": "公众号", "日期": "10-17", "内容": "某文章科普野生动物保护法修订要点，阅读量十万加。"},
    {"平台": "微博",  "日期": "10-18", "内容": "海关通报查获走私穿山甲鳞片20公斤，3人被刑事拘留。"},
    {"平台": "小红书", "日期": "10-16", "内容": "用户晒出野生兰花照片被专家指出是保护植物，已删除。"},
    {"平台": "抖音",  "日期": "10-19", "内容": "主播食用野生娃娃鱼被查处，实为人工养殖，误导宣传被处罚。"},
]
知识库指纹们 = 做指纹([块["内容"] for 块 in 知识库])
print(f"知识库就绪：{len(知识库)} 块（每块带平台/日期标签）。\n")

拒答线 = 0.40    # 上一讲你亲手调出来的

def 精排(问题, 候选们):
    """LLM 精排员：拿着问题和候选池，逐条细看，挑出最能回答问题的 2 块"""
    编号清单 = "".join(f"[{i+1}] {候选['平台']}｜{候选['日期']}｜{候选['内容']}\n"
                     for i, 候选 in enumerate(候选们))
    白板 = [
        {"role": "system", "content": "你是检索质量审核员。判断哪几条资料最能回答问题，只输出 JSON。"},
        {"role": "user", "content":
            "候选资料：\n" + 编号清单 +
            '问题：' + 问题 + '\n\n从候选里挑出最能回答问题的 2 条，只输出 JSON：{"选择": [编号, 编号]}'},
    ]
    原文 = 问模型(白板, 温度=0.1)          # 提取类任务：低温
    return json.loads(原文)["选择"]         # 结构化输出：程序直接拆包

print("=== RAG 2.0（粗排+精排+元数据）输入 q 退出 ===")
print("建议问：①穿山甲相关的舆情有哪些？②涉及处罚或法律的舆情有哪些？③平台:微博 日期:10-17以后 的舆情\n")

while True:
    问题 = input("你问：")
    if 问题 in ("q", "quit", "退出"):
        break
    if 问题 == "":
        continue

    # ---- ③ 元数据过滤：问题以"平台:"开头时，先按标签筛再搜 ----
    候选范围 = 知识库
    候选指纹 = 知识库指纹们
    if 问题.startswith("平台:"):
        零件 = 问题.split(maxsplit=1)
        条件 = 零件[0]                       # 如 平台:微博
        问题 = 零件[1] if len(零件) > 1 else ""
        平台名 = 条件.split(":")[1]
        候选范围 = [块 for 块 in 知识库 if 块["平台"] == 平台名]      # 先筛：标签硬条件
        候选指纹 = [指纹 for 块, 指纹 in zip(知识库, 知识库指纹们) if 块["平台"] == 平台名]
        print(f"[元数据过滤] 平台={平台名}：{len(知识库)} 块 → {len(候选范围)} 块")

    if not 问题:
        continue

    # ---- ② 粗排：一把尺子扫全池，取 Top-5 进候选 ----
    问题指纹 = 做指纹([问题])[0]
    排名 = sorted(range(len(候选范围)),
                  key=lambda i: -相似度(问题指纹, 候选指纹[i]))
    最高分 = 相似度(问题指纹, 候选指纹[排名[0]])
    print(f"[粗排] 候选池 Top-5（一把尺子扫全部）：")
    for 名次, 索引 in enumerate(排名[:5]):
        print(f"  [{名次+1}] {相似度(问题指纹, 候选指纹[索引]):.3f} {候选范围[索引]['平台']}｜{候选范围[索引]['内容'][:25]}……")

    if 最高分 < 拒答线:
        print(f"[拒答] 最高分 {最高分:.3f} 低于 {拒答线}：库里没有，不编。")
        continue

    # ---- ③ 精排：LLM 审核员从候选池细选 2 块 ----
    候选们 = [候选范围[i] for i in 排名[:5]]
    选择 = 精排(问题, 候选们)
    print(f"[精排] LLM 审核员选择：{选择}")
    精选 = [候选们[i - 1] for i in 选择 if 0 < i <= len(候选们)][:2]

    # ---- 组白板，带引用作答 ----
    白板 = [
        {"role": "system", "content":
            "你是舆情分析助手。只能根据【参考资料】回答，末尾用 [编号] 标注引用；"
            "资料里没有的就明说'资料中未提及'，绝不编造。"},
        {"role": "user", "content":
            "参考资料：\n" + "".join(f"[{i+1}] {块['平台']}｜{块['内容']}\n" for i, 块 in enumerate(精选)) +
            "\n问题：" + 问题},
    ]
    print(f"\nAI：{问模型(白板)}\n")

print("再见。")
