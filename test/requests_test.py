import requests
import time

while 1:
    time.sleep(0.25)
    r = requests.get('https://api.bitforex.com/api/v1/market/depth?symbol=coin-usdt-btc&size=20')
    print(r.status_code)