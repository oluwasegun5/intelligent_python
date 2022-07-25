def extra_long_factorials(n):
    f = 1
    while n > 0:
        f *= n
        n -= 1
    print(f)


if __name__ == '__main__':
    n = int(input().strip())
    extra_long_factorials(n)
