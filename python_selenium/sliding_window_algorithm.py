# string = "qewtudbdgdtdysjsncveteujmn"
# highest = 0
# checker = []
#
# for i in string:
#     j = 0
#
#     if i not in checker:
#         checker.append(i)
#         if len(checker) > highest:
#             highest = len(checker)
#     else:
#         j = checker.index(i)
#         checker = checker[j + 1::]
#         checker.append(i)
# print(highest)
nums = {1, 2, 3, 4, 5, 6}
nums.add(7)
print(nums)