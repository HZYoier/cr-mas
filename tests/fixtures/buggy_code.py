"""Bug 猎人测试 fixture——包含运行时错误的代码"""


def add_price(a, b):
    return a + b


def risky_calc(x):
    result = "total: " + x  # TypeError: str + int
    return result
