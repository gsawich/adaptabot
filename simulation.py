import traceback


class Simulation:
    def __init__(self, runtimeIndex, isActive, marketConnection, tradingConnection, Q, MARG, PAIR, LAST, LONG, SHORT, SIGNAL, SPREAD, D):
        self.runtime = runtimeIndex
        self.isActive = isActive
        self.q=Q
        self.margin = MARG
        self.pair = PAIR
        self.prices = []
        self.emaprices = []
        self.macds = []
        self.signals = []
        self.listSell = []
        self.listBuy = []
        self.currentMovingAverage = 0
        self.currentEMA = 0
        self.currentMACD = 0
        self.currentSignal = 0
        self.currentDiff = 0
        self.lastDiff = 0
        self.diffDerv = 0
        self.lengthOfMA = SHORT
        self.lengthofEMA = LONG
        self.lengthofSignal = SIGNAL
        self.timespan = 60*60*24
        self.tradePlaced = False
        self.typeOfTrade = False
        self.dataDate = ""
        self.orderNumber = ""
        self.lastTrade = LAST
        self.previousPrice = LAST
        self.mod = 1
        self.thissell = LAST
        self.thisbuy = LAST
        self.listBuy.append(LAST)
        self.listSell.append(LAST)
        self.score = 0
        self.profit = 0
        self.startTime = True
        self.endTime = int(time.time())
        self.historicalData = False
        self.spread = SPREAD
        self.tradingConn = tradingConnection
        self.marketConn = marketConnection
        self.profitActual = 0
        self.constQ = Q
        self.debug = D

    def run(self, currentValues):

            try:

                #print(currentValues['result'])
                lastPairPrice = float(currentValues['lastDealPrice'])
                lastBid = float(currentValues['buy'])
                lastAsk = float(currentValues['sell'])
                self.dataDate = datetime.datetime.now()
                #print("Bid: %s Ask: %s Last: %s" % (lastBid, lastAsk, lastPairPrice))
                if ((len(self.prices) > 0)):
                    self.currentMovingAverage = sum(self.prices) / float(len(self.prices))
                    self.currentEMA = sum(self.emaprices) / float(len(self.emaprices))
                    self.currentMACD = self.currentMovingAverage - self.currentEMA
                    self.currentSignal = sum(self.signals) / float(len(self.signals))
                    self.lastDiff = self.currentDiff
                    self.currentDiff = self.currentMACD - self.currentSignal
                    self.diffDerv = self.currentDiff - self.lastDiff
                    if (float(self.prices[-1]) != lastPairPrice):
                        self.previousPrice = float(self.prices[-1])
                    self.lastBuy = self.listBuy.pop()
                    self.lastSell = self.listSell.pop()
                    self.thisbuy = max(self.lastBuy, self.lastTrade)
                    self.thissell = min(self.lastSell, self.lastTrade)
                    self.listSell.append(self.lastSell)
                    self.listBuy.append(self.lastBuy)
                    diff = len(self.listSell) - len(self.listBuy)
                    if (diff > 1 and self.profit > 0):
                        self.profit = self.profit * (1-(diff/1000))

                    if ((self.tradePlaced==False) and (not self.historicalData)):
                        startTime = False
                        #print("first if statement passed")
                        if (self.diffDerv < 0 and self.currentDiff > 0 and lastPairPrice < self.previousPrice and lastBid > (self.thisbuy*pow(self.margin,self.mod))):
                            #print("sell if statement passed")
                            if (self.isActive == True):
                                print("SELL ORDER")
                                self.orderNumber = self.tradingConn.create_limit_order(self.pair, 'sell', self.q, lastBid-self.spread)
                                print(self.orderNumber)
                                if (self.orderNumber != False):
                                    self.tradePlaced = True
                                    self.typeOfTrade = "short"
                                    self.lastTrade = lastBid
                                    self.listSell.append(self.lastTrade)
                                    self.mod += 1
                                    #self.q *= 1 + ((self.margin-1)/4)
                                    if (len(self.listBuy) > 1): self.listBuy.pop()

                            else:
                                tradeprofit = ((lastBid-self.spread)*self.q)*0.9992
                                self.profit += tradeprofit
                                if (self.debug): print("(%s) : <<<SELL ORDER>>> for %s Profit: %s" % (self.runtime, tradeprofit, self.profit))
                                self.tradePlaced = True
                                self.typeOfTrade = "short"
                                self.lastTrade = lastBid
                                self.listSell.append(self.lastTrade)
                                self.mod += 1
                                #self.q *= 1 + ((self.margin-1)/4)
                                if (len(self.listBuy) > 1): self.listBuy.pop()
                        elif (self.diffDerv > 0 and self.currentDiff < 0 and lastPairPrice > self.previousPrice and lastAsk < (self.thissell/self.margin)):
                            #print("buy if statement passed")
                            if (self.isActive == True):
                                print("BUY ORDER")
                                self.orderNumber = self.tradingConn.create_limit_order(self.pair, 'buy', self.q, price=lastAsk+self.spread)
                                print(self.orderNumber)
                                if (self.orderNumber != False):
                                    self.tradePlaced = True
                                    self.typeOfTrade = "long"
                                    self.lastTrade = lastAsk
                                    self.listBuy.append(self.lastTrade)
                                    self.mod = 1
                                    if (len(self.listSell) > 1 ) : self.listSell.pop()
                            else:
                                tradeprofit = ((lastAsk+self.spread)*self.q)*0.9992
                                self.profit -= tradeprofit
                                if (self.debug): print("(%s) : <<<BUY ORDER>>> for %s Profit: %s" % (self.runtime, tradeprofit, self.profit))
                                self.tradePlaced = True
                                self.typeOfTrade = "long"
                                self.lastTrade = lastAsk
                                self.listBuy.append(self.lastTrade)
                                self.mod = 1
                                if (len(self.listSell) > 1 ) : self.listSell.pop()


                    elif (self.typeOfTrade == "short"):
                        if ((lastPairPrice < self.currentMovingAverage and lastPairPrice < self.currentEMA) or self.currentDiff < 0):
                            if (self.debug): print("(%s) : EXIT SHORT : %s" % (self.runtime, self.profit))
                            self.tradePlaced = False
                            self.typeOfTrade = False
                            if ((self.isActive == True) and (self.orderNumber != None)):
                                order = self.tradingConn.get_order_details(order_id=self.orderNumber['orderId'])
                                print(order)
                                deal = order['dealAmount'] * 0.9992
                                if (deal < (self.constQ/2)): deal = self.constQ
                                self.q = deal
                                print(self.q)
                                self.profit += (order['dealValueTotal'] * (0.9992))
                                self.profitActual += (order['dealValueTotal'] * 0.9992)
                                self.conn.cancel_order(order_id=self.orderNumber['orderId'])

                    elif (self.typeOfTrade == "long"):
                        if ((lastPairPrice > self.currentMovingAverage and lastPairPrice > self.currentEMA) or self.currentDiff > 0):
                            if (self.debug): print("(%s) : EXIT LONG : %s" % (self.runtime, self.profit))
                            self.tradePlaced = False
                            self.typeOfTrade = False
                            if ((self.isActive == True) and (self.orderNumber != None)):
                                order = self.conn.get_order_details(order_id=self.orderNumber['orderId'])
                                print(order)
                                self.q = round(order['dealAmount'] * (1 + ((self.margin-1)/4)), 4)
                                print(self.q)
                                self.profit -= (order['dealValueTotal'] * 0.9992)
                                self.profitActual -= (order['dealValueTotal'] * 0.9992)
                                print("Profit = %s" % (self.profit))
                                self.conn.cancel_order(order_id=self.orderNumber['orderId'])


                if (self.isActive == True):
                    print(
                        "%s %s %s %s %s %s: %s  Derivative: %s Diff: %s Target: %s / %s Profit: %s %s" %
                        (self.margin, self.lengthofEMA, self.lengthOfMA, self.lengthofSignal, self.dataDate, self.pair, lastPairPrice, self.diffDerv, self.currentDiff, self.thissell/self.margin, self.thisbuy*pow(self.margin,self.mod), self.profit, self.typeOfTrade))

                self.prices.append(float(lastPairPrice))
                self.prices = self.prices[-self.lengthOfMA:]

                self.emaprices.append(float(lastPairPrice))
                self.emaprices = self.emaprices[-self.lengthofEMA:]

                self.macds.append(float(self.currentMACD))
                self.signals = self.macds[-self.lengthofSignal:]


            except:
                print(traceback.format_exc())

            return self.profit

    def setActive(self, bool):
        self.isActive = bool
        return

    def getProfitActual(self):
        return self.profitActual

    def getQuantity(self):
        return self.q
