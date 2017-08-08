from bittrex import Bittrex
import pprint as pp

pairs = ['BTC-LBC', 'BTC-ETH', 'BTC-SC', 'BTC-XEM', 'BTC-BCC', 'BTC-OMG', 'BTC-GNT', 'BTC-NEO']

bt = Bittrex('d398b9c24bfe44419c370979b25fc257', 'dbb19df7e42a4573bad41c80712921fd')
totalprofit = 0
best = '';
highscore = 0;
for i in pairs:
    history = bt.get_order_history(i, 1000)
    #pp.pprint(history['result'][:])
    print(i)
    profit = 0;

    for x in range(len(history)):
        if history['result'][x]['OrderType'] == 'LIMIT_SELL':
            profit += history['result'][x]['Price']
        elif history['result'][x]['OrderType'] == 'LIMIT_BUY':
            profit -= history['result'][x]['Price']

    print(profit)
    if profit > highscore:
        highscore = profit
        best = i
    totalprofit += profit

usd = bt.get_ticker('USDT-BTC')['result']['Last']
print(totalprofit)
print('$',totalprofit*usd)
print("Best performer: %s with %f" % (best, highscore))
