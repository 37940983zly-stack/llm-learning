# ============================================
# 模块五第 1 课：把 mini_chat 变成 Web 服务
#
# 之前的程序：只有你能用（在你电脑终端跑）
# 现在：开一家餐厅——一直开着、等人敲门、手机也能访问
#
# 启动（终端粘贴运行）：
#   cd "/Volumes/z的磁盘/zcode/2026-10-12-llm-learning"
#   PYTHONPATH="/Volumes/z的磁盘/Codex install/fastapi" python3 -m uvicorn web_chat:app --host 0.0.0.0 --port 8000
#
# 然后浏览器打开：http://127.0.0.1:8000/docs
# ============================================

from fastapi import FastAPI
from pydantic import BaseModel
import urllib.request, urllib.error, json

with open("key.txt") as f:
    my_key = f.read().strip()

def 问(消息):
    card = {"model": "glm-4.5-flash", "temperature": 0.7,
            "messages": [{"role": "user", "content": 消息}]}
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(card).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + my_key},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"【调用失败】{e.code}"

# ---- 开餐厅：领执照 ----
app = FastAPI(title="我的第一个 Web 服务", description="小于的大模型学习·模块五")

# ---- 菜单上的第一道菜 ----
class 聊天请求(BaseModel):          # 请求卡片格式（守门员：格式不对的请求直接打回，不用进厨房）
    消息: str

@app.post("/chat")
def 聊天(请求: 聊天请求):
    回答 = 问(请求.消息)
    return {"回答": 回答}

# ---- 第二道菜：健康检查（运维标配：随时探测服务活着没）----
@app.get("/ping")
def 心跳():
    return {"状态": "活着"}
