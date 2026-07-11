
# 这是一行注释
"""这是模块文档字符串"""

def add(a, b):
    """返回两数之和"""
    return a + b

def calculate_total(items):
    """计算总价"""
    total = 0
    for item in items:
        # 累加
        total += item
    return total