

def simple():
    return 1


def complex_func(n):
    result = 0
    if n > 0:
        for i in range(n):
            if i % 2 == 0:
                if i > 10:
                    result += 1
    return result