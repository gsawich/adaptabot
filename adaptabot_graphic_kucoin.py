# Adaptabot with graphical output for automated Kucoin trading
import time
import datetime
import traceback
import math
import pygame
import connections
from simulation import Simulation


def main(Q, MARG, PAIR, LAST, LONG, SHORT, SIGNAL, SPREAD, BRANCHES):
    global profitActual
    # spawns a tribe of (branches ^ modifiables) bots with variable differences
    period = 15000
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
    tradingConn = connections.tradingClient
    marketConn = connections.marketClient
    running = True
    gridSize = math.ceil(128 / simulationSize)
    ticker = period - 1
    DEBUG = False

    for i in range(simulationSize):  # populate sim list
        mutationMatrix[0] = float(1 + ((MARG - 1) * 3 / (i + 1)))
        print(MARG * mutationMatrix[0])
        for j in range(simulationSize):
            mutationMatrix[1] = (1 + ((j - mid) / 20))
            for k in range(simulationSize):
                mutationMatrix[2] = (1 + ((k - mid) / 20))
                for l in range(simulationSize):
                    if (i == j == k == l == mid):
                        isActive = True
                        bestSim = runIndex
                    else:
                        isActive = False
                    mutationMatrix[3] = (1 + ((l - mid) / 10))
                    sim = Simulation(runIndex, isActive, marketConn, tradingConn, Q, MARG * mutationMatrix[0], PAIR,
                                     LAST, math.ceil(LONG * mutationMatrix[1]), math.floor(SHORT * mutationMatrix[2]),
                                     math.ceil(SIGNAL * mutationMatrix[3]), SPREAD, DEBUG)
                    simulationList.append(sim)
                    runIndex += 1

    # init graphics
    pygame.init()
    pygame.display.set_caption("Adaptabot 4.0: %s" % (PAIR))
    screen = pygame.display.set_mode(((simulationSize ** 2) * gridSize, (simulationSize ** 2) * gridSize))
    clock = pygame.time.Clock()
    clock.tick(10)

    while running:  # execute sims
        # event handling, gets all event from the eventqueue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False

        ticker += 1
        if (ticker % (period * 1000) == 0):
            if (ticker == (period * 1000) * 10): ticker = 0
            try:
                currentValues = marketConn.get_kline(PAIR, '1min')
                print(currentValues)
                if (ticker > 1 * period * 1000):
                    for s in simulationList:
                        thisprofit = s.run(currentValues)
                        profitArray[s] = thisprofit

                    bestProfit = max(profitArray, key=(lambda key: profitArray[key]))
                    worstProfit = min(profitArray, key=(lambda key: profitArray[key]))
                    profitActual = simulationList[bestSim].getProfitActual()
                    quantity = simulationList[bestSim].getQuantity()
                    if ((profitArray[bestProfit] > 0) and (
                            profitArray[bestProfit] > profitArray[simulationList[bestSim]]) and (
                            simulationList[bestSim].typeOfTrade == bestProfit.typeOfTrade)):
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
                        print("<<< Margin: %s Long: %s Short: %s Signal: %s Trade: %s >>>" % (
                        bestProfit.margin, bestProfit.lengthofEMA, bestProfit.lengthOfMA, bestProfit.lengthofSignal,
                        last_trade))
                    print("Current profit: %s | Best Profit: %s | Quant: %s" % (
                    profitActual, profitArray[bestProfit], quantity))

                    maxrange = max(LAST * Q, abs(profitArray[worstProfit]), abs(profitArray[bestProfit]))
                    for x in profitArray:
                        thisprofit = profitArray[x]
                        coords = pygame.Rect((x.runtime % (simulationSize ** 2)) * gridSize,
                                             (math.floor(x.runtime / (simulationSize ** 2))) * gridSize, gridSize,
                                             gridSize)
                        if (thisprofit < 0):
                            color = pygame.Color(math.floor(255 * math.sqrt(math.sqrt(abs(thisprofit) / maxrange))), 0,
                                                 0)
                        else:
                            color = pygame.Color(0, math.floor(255 * math.sqrt(math.sqrt(thisprofit / maxrange))), 0)
                        pygame.draw.rect(screen, color, coords, 0)
                        if (x.isActive == True):
                            pygame.draw.rect(screen, pygame.Color(255, 255, 255), coords, 1)
                        else:
                            pygame.draw.rect(screen, pygame.Color(0, 128, 255), coords, 1)
                        pygame.display.flip()
            except:
                print(traceback.format_exc())


if __name__ == "__main__":
    main(0.005, 1.0045, "BTC-USDT", 60000, 100, 15, 10, 0.5, 7)
