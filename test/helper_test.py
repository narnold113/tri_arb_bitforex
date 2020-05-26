import numpy as np 

# balances = [100, 300, 600, 601, 10000]
# orderbook = [[100, 1], [200, 1], [300,1], [400,1]]

# rev_balances = [10, 15, 20, np.nan]
# rev_orderbook = [[0.23, 10], [0.24, 5], [0.25, 15], [0.26, 6]]

def getWeightedPrice(orders, balance, reverse=False):
    weightedPrices = []
    for bal in balance:
        volume = 0
        price = 0
        wp = 0
        remainder = 0
        if reverse:
            for o, order in enumerate(orders):
                if np.isnan(bal):
                    weightedPrices.append(np.nan)
                    # print('Balance item in Nan')
                    break
                volume += order[1]
                wp += order[0] * (order[1] / bal)
                if volume >= bal:
                    remainder = volume - bal
                    wp -= order[0] * (remainder / bal)
                    weightedPrices.append(wp)
                    break
                elif volume < bal and o == len(orders) - 1:
                    weightedPrices.append(np.nan)
                else:
                    continue
        else:
            for o, order in enumerate(orders):
                volume += order[0] * order[1]
                wp += order[0] * ((order[0] * order[1]) / bal)
                if volume >= bal:
                    remainder = volume - bal
                    wp -= order[0] * (remainder / bal)
                    weightedPrices.append(wp)
                    break
                elif volume < bal and o == len(orders) - 1:
                    weightedPrices.append(np.nan)
                else:
                    continue

    return np.array(weightedPrices, np.float64)

# res = getWeightedPrice(rev_orderbook, rev_balances, reverse=True)
# print(res)
# print(type(res))
# print(res.dtype)