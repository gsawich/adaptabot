# Adaptbot genetic algo for bittrex
import time
import datetime
import traceback
import math
import connections

def main(Q, MARG, PAIR, LAST, LONG, SHORT, SIGNAL, SPREAD, BRANCHES):
    global profitActual
    # spawns a tribe of (branches ^ modifiables) bots with 1% differences
    period = 15
    runIndex = 0
    isActive = False
    simulationSize = BRANCHES
    simulationList = []
    modifiables = 4
    mutationMatrix = [0] * modifiables
    mid = math.floor(simulationSize / 2)
    profitArray = {}
    bestSim = 0
    profitActual = 0
    conn = connections.bittrex

    for i in range(simulationSize): #populate sim list
        mutationMatrix[0] = float(1+((MARG-1)*3/(i+1)))
        print(MARG*mutationMatrix[0])
        for j in range(simulationSize):
            mutationMatrix[1] = (1+((j - mid)/20))
            #print(math.ceil(LONG*mutationMatrix[1]))
            for k in range(simulationSize):
                mutationMatrix[2] = (1+((k-mid)/20))
                #print(math.floor(SHORT*mutationMatrix[2]))
                for l in range(simulationSize):
                    if (i == j == k == l == mid):
                        isActive = True
                        bestSim = runIndex
                    else:
                        isActive = False
                    mutationMatrix[3] = (1+((l-mid)/10))
                    #print(math.ceil(SIGNAL*mutationMatrix[3]))
                    sim = Simulation(runIndex, isActive, conn, Q, MARG*mutationMatrix[0], PAIR, LAST, math.ceil(LONG*mutationMatrix[1]), math.floor(SHORT*mutationMatrix[2]), math.ceil(SIGNAL*mutationMatrix[3]), SPREAD)
                    simulationList.append(sim)
                    runIndex += 1

    while True: #execute sims

        try:
            currentValues = conn.get_ticker(PAIR)

            for s in simulationList:
                thisprofit = s.run(currentValues)
                profitArray[s] = thisprofit
            bestProfit = max(profitArray, key=(lambda key: profitArray[key]))
            profitActual = simulationList[bestSim].getProfitActual()
            #print(bestProfit)
            if ((profitArray[bestProfit] > 0) and (profitArray[bestProfit] > profitArray[simulationList[bestSim]]) and (simulationList[bestSim].typeOfTrade == bestProfit.typeOfTrade)):
                simulationList[bestSim].setActive(False)
                last_trade = simulationList[bestSim].lastTrade
                trade_order = simulationList[bestSim].orderNumber
                trade_mod = simulationList[bestSim].mod
                trade_q = simulationList[bestSim].q
                bestSim = bestProfit.runtime
                bestProfit.setActive(True)
                bestProfit.lastTrade = last_trade
                bestProfit.mod = trade_mod
                bestProfit.q = trade_q
                bestProfit.listSell.append(last_trade)
                bestProfit.listBuy.append(last_trade)
                bestProfit.orderNumber = trade_order
                bestProfit.profitActual = profitActual
                print("Margin: %s Long: %s Short: %s Signal: %s Trade: %s" % (bestProfit.margin, bestProfit.lengthofEMA, bestProfit.lengthOfMA, bestProfit.lengthofSignal, last_trade))
            print("Current profit: %s Best Profit: %s" % (profitActual, profitArray[bestProfit]))

        except:
            print(traceback.format_exc())

        time.sleep(int(period))


class Simulation:
    def __init__(self, runtimeIndex, isActive, connection, Q, MARG, PAIR, LAST, LONG, SHORT, SIGNAL, SPREAD):
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
        self.conn = connection
        self.profitActual = 0

    def run(self, currentValues):

            try:

                #print(currentValues['result'])
                lastPairPrice = float(currentValues['result']['Last'])
                lastBid = float(currentValues['result']['Bid'])
                lastAsk = float(currentValues['result']['Ask'])
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
                    if (diff > 0):
                        self.profit = self.profit * (1-(diff/1000))

                    if ((self.tradePlaced==False) and (not self.historicalData)):
                        startTime = False
                        #print("first if statement passed")
                        if (self.diffDerv < 0 and self.currentDiff > 0 and lastPairPrice < self.previousPrice and lastBid > (self.thisbuy*pow(self.margin,self.mod))):
                            #print("sell if statement passed")
                            if (self.isActive == True):
                                print("SELL ORDER")
                                self.orderNumber = self.conn.sell_limit(self.pair, quantity=self.q, rate=lastBid-self.spread)
                                print(self.orderNumber)
                                if (self.orderNumber['success'] != False):
                                    self.tradePlaced = True
                                    self.typeOfTrade = "short"
                                    self.lastTrade = lastBid
                                    self.listSell.append(self.lastTrade)
                                    self.mod += 1
                                    self.q *= 1 + ((self.margin-1)/4)
                                    if (len(self.listBuy) > 1): self.listBuy.pop()

                            else:
                                tradeprofit = ((lastBid-self.spread)*self.q)*0.9975
                                self.profit += tradeprofit
                                print("(%s) : <<<SELL ORDER>>> for %s Profit: %s" % (self.runtime, tradeprofit, self.profit))
                                self.tradePlaced = True
                                self.typeOfTrade = "short"
                                self.lastTrade = lastBid
                                self.listSell.append(self.lastTrade)
                                self.mod += 1
                                self.q *= 1 + ((self.margin-1)/4)
                                if (len(self.listBuy) > 1): self.listBuy.pop()
                        elif (self.diffDerv > 0 and self.currentDiff < 0 and lastPairPrice > self.previousPrice and lastAsk < (self.thissell/self.margin)):
                            #print("buy if statement passed")
                            if (self.isActive == True):
                                print("BUY ORDER")
                                self.orderNumber = self.conn.buy_limit(self.pair, quantity=self.q, rate=lastAsk+self.spread)
                                print(self.orderNumber)
                                if (self.orderNumber['success'] != False):
                                    self.tradePlaced = True
                                    self.typeOfTrade = "long"
                                    self.lastTrade = lastAsk
                                    self.listBuy.append(self.lastTrade)
                                    self.mod = 1
                                    if (len(self.listSell) > 1 ) : self.listSell.pop()
                            else:
                                tradeprofit = ((lastAsk+self.spread)*self.q)*1.0025
                                self.profit -= tradeprofit
                                print("(%s) : <<<BUY ORDER>>> for %s Profit: %s" % (self.runtime, tradeprofit, self.profit))
                                self.tradePlaced = True
                                self.typeOfTrade = "long"
                                self.lastTrade = lastAsk
                                self.listBuy.append(self.lastTrade)
                                self.mod = 1
                                if (len(self.listSell) > 1 ) : self.listSell.pop()


                    elif (self.typeOfTrade == "short"):
                        if ((lastPairPrice < self.currentMovingAverage and lastPairPrice < self.currentEMA) or self.currentDiff < 0):
                            print("(%s) : EXIT SHORT : %s" % (self.runtime, self.profit))
                            self.tradePlaced = False
                            self.typeOfTrade = False
                            if ((self.isActive == True) and (self.orderNumber['result'] != None)):
                                order = self.conn.get_order(self.orderNumber['result']['uuid'])
                                print(order)
                                self.profit += (order['result']['Price'] - order['result']['CommissionPaid'])
                                self.profitActual += (order['result']['Price'] - order['result']['CommissionPaid'])
                                self.conn.cancel(self.orderNumber['result']['uuid'])

                    elif (self.typeOfTrade == "long"):
                        if ((lastPairPrice > self.currentMovingAverage and lastPairPrice > self.currentEMA) or self.currentDiff > 0):
                            print("(%s) : EXIT LONG : %s" % (self.runtime, self.profit))
                            self.tradePlaced = False
                            self.typeOfTrade = False
                            if ((self.isActive == True) and (self.orderNumber['result'] != None)):
                                order = self.conn.get_order(self.orderNumber['result']['uuid'])
                                print(order)
                                self.profit -= (order['result']['Price'] + order['result']['CommissionPaid'])
                                self.profitActual -= (order['result']['Price'] + order['result']['CommissionPaid'])
                                print("Profit = %s" % (self.profit))
                                self.conn.cancel(self.orderNumber['result']['uuid'])

                #else:
                #    previousPrice = 0

                if (self.isActive == True):
                    print(
                        "%s %s %s %s: %s MA: %s EMA: %s Derivative: %s Diff: %s Target: %s / %s Profit: %s %s" %
                        (self.isActive, self.runtime, self.dataDate, self.pair, lastPairPrice, self.currentMovingAverage,
                         self.currentEMA, self.diffDerv, self.currentDiff, self.thissell/self.margin, self.thisbuy*pow(self.margin,self.mod), self.profit, self.typeOfTrade))


                self.prices.append(float(lastPairPrice))
                self.prices = self.prices[-self.lengthOfMA:]

                self.emaprices.append(float(lastPairPrice))
                self.emaprices = self.emaprices[-self.lengthofEMA:]

                self.macds.append(float(self.currentMACD))
                #for i in range(len(macds)):
                #    macds[i] /= (i+1)
                self.signals = self.macds[-self.lengthofSignal:]


            except:
                print(traceback.format_exc())
                #print("Server timeout ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Resolving")

            return self.profit

    def setActive(self, bool):
        self.isActive = bool
        return

    def getProfitActual(self):
        return self.profitActual

while True:
    main(1000, 1.0065, "BTC-XLM", 0.00003920, 76, 14, 12, 0.00000001, 5)