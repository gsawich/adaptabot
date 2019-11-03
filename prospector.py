import time
import datetime
import traceback
import connections

def main(Q, MARG, PAIR, LAST, LONG, SHORT, SIGNAL, SPREAD):


    q=Q
    margin = MARG
    period = 15
    pair = PAIR
    prices = []
    emaprices = []
    macds = []
    signals = []
    listSell = []
    listBuy = []
    currentMovingAverage = 0
    currentEMA = 0
    currentMACD = 0
    currentSignal = 0
    currentDiff = 0
    lastDiff = 0
    diffDerv = 0
    lengthOfMA = SHORT
    lengthofEMA = LONG
    lengthofSignal = SIGNAL
    timespan = 60*60*24
    startTime = True
    endTime = int(time.time())
    historicalData = False
    tradePlaced = False
    typeOfTrade = False
    dataDate = ""
    orderNumber = ""
    lastTrade = LAST
    previousPrice = LAST
    mod = 1
    conn = connections.bittrex
    thissell = LAST
    thisbuy = LAST
    listBuy.append(LAST)
    listSell.append(LAST)
    score = 0
    profit = 0

    while True:
        if (startTime and historicalData):
            nextDataPoint = historicalData.pop(0)
            lastPairPrice = nextDataPoint['weightedAverage']
            lastBid = lastPairPrice
            lastAsk = lastPairPrice
            dataDate = datetime.datetime.fromtimestamp(int(nextDataPoint['date'])).strftime('%Y-%m-%d %H:%M:%S')
        else:
            try:
                currentValues = conn.get_ticker(pair)

                #print(currentValues['result'])
                lastPairPrice = float(currentValues['result']['Last'])
                lastBid = float(currentValues['result']['Bid'])
                lastAsk = float(currentValues['result']['Ask'])
                dataDate = datetime.datetime.now()
                print("Bid: %s Ask: %s Last: %s" % (lastBid, lastAsk, lastPairPrice))
                if ((len(prices) > 0)):
                    currentMovingAverage = sum(prices) / float(len(prices))
                    currentEMA = sum(emaprices) / float(len(emaprices))
                    currentMACD = currentMovingAverage - currentEMA
                    currentSignal = sum(signals)/ float(len(signals))
                    lastDiff = currentDiff
                    currentDiff = currentMACD - currentSignal
                    diffDerv = currentDiff - lastDiff
                    if (float(prices[-1]) != lastPairPrice):
                        previousPrice = float(prices[-1])
                    lastBuy = listBuy.pop()
                    lastSell = listSell.pop()
                    thisbuy = max(lastBuy, lastTrade)
                    thissell = min(lastSell, lastTrade)
                    listSell.append(lastSell)
                    listBuy.append(lastBuy)
                    if ((tradePlaced==False) and (not historicalData)):
                        startTime = False
                        if (diffDerv < 0 and currentDiff > 0 and lastPairPrice < previousPrice and lastBid > (thisbuy*pow(margin,mod))):
                            print("SELL ORDER")
                            orderNumber = conn.sell_limit(pair, quantity=q, rate=lastBid-SPREAD)
                            print(orderNumber)
                            if (orderNumber['success'] != False):
                                tradePlaced = True
                                typeOfTrade = "short"
                                lastTrade = lastBid
                                listSell.append(lastTrade)
                                mod += 1
                                q *= 1 + ((margin-1)/2)
                                if (len(listBuy) > 1): listBuy.pop()
                        elif (diffDerv > 0 and currentDiff < 0 and lastPairPrice > previousPrice and lastAsk < (thissell/margin)):
                            print("BUY ORDER")
                            orderNumber = conn.buy_limit(pair, quantity=q, rate=lastAsk+SPREAD)
                            print(orderNumber)
                            if (orderNumber['success'] != False):
                                tradePlaced = True
                                typeOfTrade = "long"
                                lastTrade = lastAsk
                                listBuy.append(lastTrade)
                                mod = 1
                                if (len(listSell) > 1 ) : listSell.pop()


                    elif (typeOfTrade == "short"):
                        if ((lastPairPrice < currentMovingAverage and lastPairPrice < currentEMA) or currentDiff < 0):
                            print("EXIT SHORT")
                            if (orderNumber['result'] != None):
                                order = conn.get_order(orderNumber['result']['uuid'])
                                print(order)
                                profit += order['result']['Price']
                                conn.cancel(orderNumber['result']['uuid'])

                            tradePlaced = False
                            typeOfTrade = False
                    elif (typeOfTrade == "long"):
                        if ((lastPairPrice > currentMovingAverage and lastPairPrice > currentEMA) or currentDiff > 0):
                            print("EXIT LONG")
                            if (orderNumber['result'] != None):
                                order = conn.get_order(orderNumber['result']['uuid'])
                                print(order)
                                profit -= order['result']['Price']
                                print("Profit = %s" % (profit))
                                conn.cancel(orderNumber['result']['uuid'])
                            tradePlaced = False
                            typeOfTrade = False

                print(
                    "%s %s: %s Q: %s Derivative: %s Diff: %s Target: %s / %s Profit: %s" % (dataDate, pair, lastPairPrice, q, diffDerv, currentDiff, thissell/margin, thisbuy*pow(margin,mod), profit))


                prices.append(float(lastPairPrice))
                prices = prices[-lengthOfMA:]

                emaprices.append(float(lastPairPrice))
                emaprices = emaprices[-lengthofEMA:]

                macds.append(float(currentMACD))
                signals = macds[-lengthofSignal:]



                if (not startTime):
                    time.sleep(int(period))
            except:
                print(traceback.format_exc())
while True:
    main(.5, 1.025, "USDT-BCC", 1424, 200, 100, 50, 0.1)