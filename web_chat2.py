# ============================================
# 模块五第 2 课：堂食区（聊天页面）+ 账本（SQLite 记性）
#
# 启动：
#   cd "/Volumes/z的磁盘/zcode/2026-10-12-llm-learning"
#   PYTHONPATH="/Volumes/z的磁盘/Codex install/fastapi" python3 -m uvicorn web_chat2:app --host 0.0.0.0 --port 8000
#
# 浏览器打开：http://127.0.0.1:8000/   ← 直接是聊天界面
# 关服务：Control + C；重启后历史仍在（账本 chat.db 记着呢）
# ============================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import urllib.request, urllib.error, json, sqlite3, datetime

with open("key.txt") as f:
    my_key = f.read().strip()

# ===== 账本：SQLite（Python 自带，一个文件一个库）=====
库 = sqlite3.connect("chat.db", check_same_thread=False)   # FastAPI 在别的线程里跑，需允许跨线程用这本账
库.execute("""CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT, content TEXT, time TEXT)""")   # 表=账本里的一页表格；一行一条记录
库.commit()

def 记账(谁, 内容):
    库.execute("INSERT INTO messages (role, content, time) VALUES (?, ?, ?)",   # SQL：存=INSERT
               (谁, 内容, datetime.datetime.now().strftime("%m-%d %H:%M")))
    库.commit()

def 翻账(条数=20):
    行们 = 库.execute("SELECT role, content, time FROM messages ORDER BY id DESC LIMIT ?",   # SQL：取=SELECT
                      (条数,)).fetchall()
    return [{"谁": r, "内容": c, "时间": t} for r, c, t in reversed(行们)]

def 问(白板):
    card = {"model": "glm-4.5-flash", "temperature": 0.7, "messages": 白板}
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

app = FastAPI(title="带记性的聊天服务")

# ===== 堂食区：浏览器直接看到的聊天页面 =====
页面 = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>小于的AI聊天</title>
<style>
 body{font-family:-apple-system,sans-serif;max-width:640px;margin:0 auto;padding:16px;background:#f5f5f5}
 h3{color:#333;text-align:center}
 #记录{height:55vh;overflow-y:auto;background:#fff;border-radius:12px;padding:12px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
 .泡{margin:8px 0;padding:8px 12px;border-radius:12px;max-width:80%;white-space:pre-wrap;line-height:1.5}
 .user{background:#95ec69;margin-left:auto;width:fit-content}
 .ai{background:#eee;width:fit-content}
 .时间{font-size:10px;color:#999;margin:0 4px}
 #输入区{display:flex;gap:8px;margin-top:10px}
 input{flex:1;padding:10px;border:1px solid #ddd;border-radius:8px;font-size:15px}
 button{padding:10px 18px;background:#07c160;color:#fff;border:none;border-radius:8px;font-size:15px}
</style></head><body>
<h3>小于的 AI 聊天（带记性版）</h3>
<div id="记录"></div>
<div id="输入区"><input id="消息" placeholder="说点什么…" autofocus><button onclick="发()">发送</button></div>
<script>
async function 读历史(){
  const r = await fetch('/history'); const data = await r.json();
  data.历史.forEach(m=>{
    const d=document.createElement('div'); d.className='泡 '+(m.谁==='user'?'user':'ai');
    d.textContent=m.内容; document.getElementById('记录').appendChild(d);
    const t=document.createElement('div'); t.className='时间'; t.textContent=m.时间;
    document.getElementById('记录').appendChild(t);
  });
  document.getElementById('记录').scrollTop=99999;
}
async function 发(){
  const 框=document.getElementById('消息'); const 文=框.value; if(!文)return; 框.value='';
  const u=document.createElement('div'); u.className='泡 user'; u.textContent=文;
  document.getElementById('记录').appendChild(u);
  const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({消息:文})});
  const data=await r.json();
  const a=document.createElement('div'); a.className='泡 ai'; a.textContent=data.回答;
  document.getElementById('记录').appendChild(a);
  document.getElementById('记录').scrollTop=99999;
}
读历史();
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
def 堂食区():
    return 页面

class 聊天请求(BaseModel):
    消息: str

@app.post("/chat")
def 聊天(请求: 聊天请求):
    历史 = 翻账(10)                                                    # 先翻账：最近10条
    白板 = [{"role": m["谁"], "content": m["内容"]} for m in 历史]      # 抄上白板
    白板.append({"role": "user", "content": 请求.消息})                  # 再添上这句新话
    回答 = 问(白板)
    记账("user", 请求.消息)       # 客人的话记账
    记账("assistant", 回答)       # AI 的回话也记账
    return {"回答": 回答}

@app.get("/history")
def 历史():
    return {"历史": 翻账(20)}

@app.get("/ping")
def 心跳():
    return {"状态": "活着"}
