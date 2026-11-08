# ===== 装箱说明书（Dockerfile）=====
# 把整个厨房装进集装箱：系统+依赖+代码，一条命令开张

# 第1步：选一块地基——官方迷你版 Python 3.9（自带干净的系统）
FROM python:3.9-slim

# 第2步：把购物单和菜谱（依赖清单+全部代码）搬进箱内
COPY requirements.txt .
COPY web_chat2.py .

# 第3步：在箱内按购物单采购安装（容器里直接装标准位置，不用 PYTHONPATH 了）
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 第4步：声明开箱营业的命令（餐厅开门即启动服务）
CMD ["python3", "-m", "uvicorn", "web_chat2:app", "--host", "0.0.0.0", "--port", "8000"]
