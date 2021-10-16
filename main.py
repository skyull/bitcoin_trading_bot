import websocket, numpy as np, json
from talib import abstract
import inspect


def buy(allocated_money, price):
    global portfolio, money_end
    quantity = allocated_money / price
    money_end = money_end - allocated_money - transaction_cost * allocated_money
    portfolio += quantity
    if investment == []:
        investment.append(allocated_money)
    else:
        investment.append(allocated_money)
        investment[-1] += investment[-2]


def sell(allocated_money, price):
    global portfolio, money_end
    quantity = allocated_money / price
    money_end = money_end + allocated_money - transaction_cost * allocated_money
    portfolio -= quantity  
    investment.append(-allocated_money)
    investment[-1] += investment[-2]


def on_message(ws, message):
    global portfolio, investment, closes, highs, lows, money_end, core_to_trade, core_quantity, real_time_portfolio_value
    json_message = json.loads(message)
    cs = json_message['k']
    candle_closed, close, high, low, open, volume = cs['x'], cs['c'], cs['h'], cs['l'], cs['o'], cs['v']
    candle = [open, high, low, close, volume]

    if candle_closed:

        # Add new candle to the list
        for i in candles:
            i.append(float(candle[candles.index(i)]))

        # Format input for abstract talib
        inputs = {'open': np.array(opens),
                  'high': np.array(highs),
                  'low': np.array(lows),
                  'close': np.array(closes),
                  'volume': np.array(volumes),
                  }

        # First buy
        if core_to_trade:
            buy(core_trade_amount, closes[-1])
            print(f'Core investment: we bought ${core_trade_amount} worth of bitcoin')
            core_quantity += core_trade_amount / closes[-1]
            core_to_trade = False


        # Get all talib pattern indicators
        indicators = []
        for method in public_method_names:
            indicator = getattr(abstract, method)(inputs)
            indicators.append(indicator[-1])

        # Get the average of indicators
        avg_indicators = np.mean(indicators)


        if avg_indicators >= 10:
            amt = trade_amount
        elif avg_indicators <= -10:
            amt = -trade_amount
        else:
            amt = avg_indicators * 10

        # Update portfolio value
        port_value = portfolio * closes[-1] - core_quantity * closes[-1]
        trade_amt = amt - port_value
        RT_portfolio_value = money_end + portfolio * closes[-1]
        real_time_portfolio_value.append(float(RT_portfolio_value))

        print(f'Average of all indicators: {avg_indicators}, recommended exposure: ${amt}')
        print(f'Real-time portfolio value: ${RT_portfolio_value}')
        print(f'Invested amount: ${portfolio * closes[-1]}')

        if trade_amt > min_trade_amt:
            buy(trade_amt, closes[-1])
            print(f'We bought ${trade_amt} worth of bitcoin')
        elif trade_amt < -min_trade_amt:
            sell(-trade_amt, closes[-1])
            print(f'We sell ${trade_amt} worth of bitcoin')

if __name__ == '__main__':


    cc = 'btcusd'   # Market to trade


    interval = '1m' # Duration of the candle


    socket = f'wss://stream.binance.com:9443/ws/{cc}t@kline_{interval}' # Binance web socket addr


    amount = 1000   # Initial $ amount invested

    # Initial core invested (first buy)
    core_trade_amount = amount * 0.9
    core_quantity = 0

    # Volatile trade amount
    trade_amount = amount * 0.1

    # Trade core to True for first buy
    core_to_trade = True

    # Transaction cost for each $
    transaction_cost = 0.0005

    # Minimum trading amount
    min_trade_amt = 30


    portfolio = 0

    investment, real_time_portfolio_value, closes, highs, lows, opens, volumes = [], [], [], [], [], [], [],
    money_end = amount
    candles = [opens, highs, lows, closes, volumes]



    public_method_names = [method for method in dir(abstract) if method.startswith('CDL')]

    ws = websocket.WebSocketApp(socket, on_message=on_message)
    ws.run_forever()


    print(investment)
    port_value = portfolio * closes[-1]
    if port_value > 0:
        sell(port_value, closes[-1])
    else:
        buy(-port_value, closes[-1])

    money_end += investment[-1]
    print('All trades settled')

    print(money_end)
    print(portfolio)

    # Return and Risk comparison with benchmark, risk adjusted return calculation: sharpe ratio

    beg = closes[0]
    end = closes[-1]

    btc_return = np.mean(np.log(np.array(closes[1:]) / np.array(closes[:-1])))
    bot_return = np.mean(np.log(np.array(real_time_portfolio_value[1:]) / np.array(real_time_portfolio_value[:-1])))
    alpha = bot_return - btc_return
    btc_risk = np.std(np.log(np.array(closes[1:]) / np.array(closes[:-1])))
    bot_risk = np.std(np.log(np.array(real_time_portfolio_value[1:]) / np.array(real_time_portfolio_value[:-1])))
    btc_sharpe_ratio = round(btc_return / btc_risk, 3)
    bot_sharpe_ratio = round(bot_return / bot_risk, 3)

    print(f'btc return: {btc_return}, btc_risk: {btc_risk}, btc_sharpe_ratio: {btc_sharpe_ratio}')
    print(f'bot_return: {bot_return}, bot_risk: {bot_risk}, bot_sharpe_ratio: {bot_sharpe_ratio}')
    print(f'alpha: {alpha}')
