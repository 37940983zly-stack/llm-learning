# ============================================
# 真正的测试文件（pytest 版）
# 规矩：文件名以 test_ 开头，pytest 会自动发现它
# 每个测试是一个 test_ 开头的函数——pytest 自动逐个跑
# 跑法：PYTHONPATH="..." python3 -m pytest test_web_chat2.py -v
# ============================================

import web_chat2   # 把我们的服务当零件导入（导入时会连上 chat.db）

def test_翻账返回清单():
    结果 = web_chat2.翻账(5)
    assert isinstance(结果, list)          # 翻出来的应该是清单

def test_记账后条数变多():
    之前 = len(web_chat2.翻账(100))
    web_chat2.记账("user", "【测试】pytest 来过")
    之后 = len(web_chat2.翻账(100))
    assert 之后 == 之前 + 1                 # 记一笔，账上多一行

def test_心跳活着():
    assert web_chat2.心跳() == {"状态": "活着"}   # 心跳接口该说活着
