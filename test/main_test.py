import json
import asyncio
import websockets
import numpy as np
import helper_test as helper
import logging
import traceback as tb
import mysql.connector
import random
import time
from datetime import datetime
from mysql.connector import Error
from mysql.connector import errorcode

balances = [1_000, 10_000, 25_000, 50_000]

ARBS = [
    'eth'
]
PAIRS = []
for arb in ARBS:
    PAIRS.append('coin-usdt-' + str.lower(arb))
    PAIRS.append('coin-btc-' + str.lower(arb))
PAIRS.insert(0, 'coin-usdt-btc')
# print(PAIRS)
SIDES = [
    'asks',
    'bids'
]

btc_book = {
    'orderbook': {
        'asks': [],
        'bids': []
    },
    'weighted_prices': {
        'regular': 0,
        'reverse': 0
    },
    'amount_if_bought': []
}
arbitrage_book = {
    arb: {
        'orderbooks': {
            pair: {}
            for pair in PAIRS if pair[-3:] == arb
        },
        'regular': { ### Regular arbitrage order: buy BTC/USD, buy ALT/BTC and sell ALT/USD. For buys, we calculate weighted price on the "ask" side ###
            'weighted_prices': {
                pair: 0
                for pair in PAIRS if pair[-3:] == arb # or pair == 'BTCUSD'
            },
            'triangle_values': []
        },
        'reverse': { ### Reverse arbitrage order: sell BTC/USD, sell ALT/BTC and buy ALT/USD. For sells, we consume the "bid" side of the orderbook ###
            'weighted_prices': {
                pair: 0
                for pair in PAIRS if pair[-3:] == arb # or pair == 'BTCUSD'
            },
            'triangle_values': [],
            'amount_if_bought': []
        }
    }
    for arb in ARBS
}
# print(arbitrage_book)

async def dataHandler(res, pair):
    global arbitrage_book
    global btc_book
    res = json.loads(res)
    for side in SIDES:
        res_length = len(res['data'][side])
        if pair == 'coin-usdt-btc':
            btc_book['orderbook'][side] =np.zeros((res_length, 2))
            for i, item in enumerate(res['data'][side]):
                btc_book['orderbook'][side][i] = np.array([item['price'], item['amount']], np.float64)
        else:
            arb1 = pair[-3:]
            arbitrage_book[arb1]['orderbooks'][pair][side] = np.zeros((res_length, 2))
            for j, jtem in enumerate(res['data'][side]):
                arbitrage_book[arb1]['orderbooks'][pair][side][j] = np.array([jtem['price'], jtem['amount']], np.float64)

async def populateArbValues():
    global btc_book
    global arbitrage_book

    await asyncio.sleep(10)
    try:
        #connect to mariadb here
        while 1:
            await asyncio.sleep(2)
            for side in SIDES:
                if side == 'asks':
                    btc_book['weighted_prices']['regular'] = helper.getWeightedPrice(btc_book['orderbook'][side], balances, reverse=False)
                else:
                    btc_book['weighted_prices']['reverse'] = helper.getWeightedPrice(btc_book['orderbook'][side], balances, reverse=False)
                btc_book['amount_if_bought'] = np.divide(balances,btc_book['weighted_prices']['regular'])

            for arb in ARBS:
                for pair in sorted(arbitrage_book[arb]['regular']['weighted_prices'], reverse=True):
                    for side in SIDES:
                        arb_ob = arbitrage_book[arb]['orderbooks'][pair][side]
                        if side == 'asks':
                            if pair[5:9] == 'usdt':
                                arbitrage_book[arb]['reverse']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob, balances, reverse=False)
                                arbitrage_book[arb]['reverse']['amount_if_bought'] = np.divide(balances, arbitrage_book[arb]['reverse']['weighted_prices'][pair])
                            else:
                                arbitrage_book[arb]['regular']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob, btc_book['amount_if_bought'], reverse=False)
                        else:
                            if pair[5:9] == 'usdt':
                                arbitrage_book[arb]['regular']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob, balances, reverse=False)
                            else:
                                arbitrage_book[arb]['reverse']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob, arbitrage_book[arb]['reverse']['amount_if_bought'], reverse=True)
                # print(btc_book['weighted_prices'])
                # print(arbitrage_book[arb]['regular']['weighted_prices']) 
                # print(arbitrage_book[arb]['reverse']['weighted_prices'])
                # print('\n')
                
                regular_arb_price = np.multiply(btc_book['weighted_prices']['regular'], arbitrage_book[arb]['regular']['weighted_prices']['coin-btc-'+arb])
                reverse_arb_price = np.divide(arbitrage_book[arb]['reverse']['weighted_prices']['coin-usdt-'+arb], arbitrage_book[arb]['reverse']['weighted_prices']['coin-btc-'+arb])
                arbitrage_book[arb]['regular']['triangle_values'] = np.nan_to_num(np.divide(np.subtract(arbitrage_book[arb]['regular']['weighted_prices']['coin-usdt-'+arb], regular_arb_price), regular_arb_price))
                arbitrage_book[arb]['reverse']['triangle_values'] = np.nan_to_num(np.divide(np.subtract(btc_book['weighted_prices']['reverse'],reverse_arb_price), reverse_arb_price))

                print(arb, 'regular', [100 * x for x in arbitrage_book[arb]['regular']['triangle_values']])
                print(arb, 'reverse', [100 * y for y in arbitrage_book[arb]['reverse']['triangle_values']]) 
                print('\n\n')
                 

    except Exception:
        tb.print_exc()
async def printBook():
    global btc_book
    global arbitrage_book

    await asyncio.sleep(10)
    # print(btc_book)
    while 1:
        await asyncio.sleep(2)
        print(arbitrage_book['eth']['orderbooks']['coin-usdt-eth']['asks'][0:5])

async def subscribeToBook(pair):
    url = 'wss://www.bitforex.com/mkapi/coinGroup1/ws'
    strParams = '[{"type":"subHq","event":"depth10","param":{"businessType":"placeholder", "dType":0}}]'
    jsonParams = json.loads(strParams)
    jsonParams[0]['param']['businessType'] = pair
    # print(jsonParams[0])
    try:
        async with websockets.client.connect(url) as websocket:
            await websocket.send(str(jsonParams).replace('\'', '"'))
            while 1:
                res = await websocket.recv()
                # print(res)
                await dataHandler(res, pair)
    except Exception:
        tb.print_exc()

async def main() -> None:
    # pass
    coroutines = [
        loop.create_task(subscribeToBook(pair))
        for pair in PAIRS
    ]
    # coroutines.append(printBook())
    coroutines.append(populateArbValues())
    await asyncio.wait(coroutines)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()











# str([{"type":"subHq","event":"depth10","param":{"businessType":"coin-btc-eth", "dType":0}}])