# ARBS = [
#     'eth'
# ]
# PAIRS = []
# for arb in ARBS:
#     PAIRS.append('coin-usdt-' + str.lower(arb))
#     PAIRS.append('coin-btc-' + str.lower(arb))
# PAIRS.insert(0, 'coin-usdt-btc')
# # print(PAIRS)

# for arb in ARBS:
#     for pair in PAIRS:
#         print(pair[5:9])
#         # if pair[-3:] == arb:
#         #     print(arb, pair)




import numpy as np

# x = np.array([10,30,40,50, np.nan])
# y = np.array([1,2,3,4, np.nan])
# divide_out = np.divide(x,y)
# print(divide_out)

# x = np.array([10,30,40,50, np.nan])
# y = np.array([1,2,3,4, np.nan])
# multiply_out = np.multiply(x,y)
# print(multiply_out)

x = np.array([10,30,40,50, np.nan])
y = np.array([1,2,3,4,5])
z = np.array([10, 10, 10, 10, np.nan])
subtract_out = np.subtract(x,y)
final_output = np.divide(np.subtract(x,y), z)
print(subtract_out)
print(final_output)