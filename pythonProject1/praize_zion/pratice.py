def non_duplicate(array) -> list:
    new_list = []
    for number in array:
        if number not in new_list:
            new_list.append(number)
    return new_list


def another(array: list) -> list:
    i = 0
    temp = []
    while i < len(array) - 1:
        if len(temp) == 0:
            temp.append(array[i])
        else:
            if array[i] > temp[-1]:
                temp.append(array[i])
        i += 1

    return temp


def real_one(array: list) -> list:
    count = 0
    i = 1

    while i < len(array):
        if array[i] > array[count]:
            array[count + 1] = array[i]
            count += 1
        elif array[i] <= array[count]:
            array[i] = 0
        i += 1


if __name__ == "__main__":
    oya = [1, 1, 2, 2, 2, 2, 3, 3, 3, 5, 5, 6, 6, 6, 6, 6, 7, 8, 9, 9, 9, 9]
    print(non_duplicate(oya))
    print(another(oya))

    print(oya)
    real_one(oya)
    print(oya)
    