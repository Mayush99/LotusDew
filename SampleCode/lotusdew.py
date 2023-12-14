# from websocket import create_connection, WebSocketConnectionClosedException
import json
# from websocket_connect import get_api_key
import ssl
import websocket
import csv
import time
import numpy as np

# Check and Establish connection with websocket
ws = websocket.create_connection("wss://api.airalgo.com/socket/websocket", sslopt={"cert_reqs": ssl.CERT_NONE})


# Payload to authenticate with the websocket
conn = {
    "topic" : "api:join",
    "event" : "phx_join",
    "payload" :
        {
            "phone_no" : "9971723017" #"1234567890"
        },
    "ref" : ""
    }

# Authenticate with websocket
ws.send(json.dumps(conn))
print(ws.recv())

while True:
    print(json.loads(ws.recv()))

# get price data for nifty 50 stocks
nifty50 = open("../ind_nifty50list.csv")
csvreader = csv.reader(nifty50)
header = []
header = next(csvreader)
rows = []
for row in csvreader:
    rows.append(row)

tickers = []
for row in rows:
    tickers.append(row[2])

tickers = tickers[:10]
# tickers = ["ADANIENT"]

data_dict = {}

for i in range(300):
    for t in range(len(tickers)):
        payload = {
            "topic" : "api:join",
            "event" : "ltp_quote", 
            "payload" : [tickers[t]], 
            "ref" : ""
            }
        ws.send(json.dumps(payload))
        data = json.loads(ws.recv())
        key = data["payload"][0]["symbol"]
        if data["payload"][0]["symbol"] not in data_dict:
            data_dict[key] = {'prices': [], 'differences': []}

        data_dict[key]['prices'].append(data["payload"][2])
        # Check if the count of prices exceeds the threshold
        if len(data_dict[key]['prices']) > 300:
            data_dict[key]['prices'].pop(0)

        # Calculate differences between consecutive prices
        if len(data_dict[key]['prices']) > 1:
            differences = data_dict[key]['prices'][-1] - data_dict[key]['prices'][-2]
            data_dict[key]['differences'].append(differences)

        # Check if the count of differences exceeds 299
        if len(data_dict[key]['differences']) > 299:
            # Pop the first element to maintain the count
            data_dict[key]['differences'].pop(0)

        # timestamp.append()
        time.sleep(1)
    time.sleep(0.5)

# print(data_dict)

all_differences = [difference for symbol_data in data_dict.values() for difference in symbol_data['differences']]
percentile_95 = np.percentile(all_differences, 95, axis = 0)

best_95th_percentile_symbols = []
for symbol, symbol_data in data_dict.items():
    for i in range(len(symbol_data['differences'])):    
        if symbol_data['differences'][i]>percentile_95:
            best_95th_percentile_symbols.append(symbol)
            break

print(best_95th_percentile_symbols)

stocksBought = {}
for t in tickers:
    stocksBought[t] = {"buy":0, "time":300, "buyingPrice":0}

# buy = 0 - not bought

profit = 0
while True:
    for symbol in best_95th_percentile_symbols:
        if stocksBought[symbol]["buy"]==0:
            payload = {
            "topic" : "api:join",
            "event" : "ltp_quote", 
            "payload" : [symbol], 
            "ref" : ""
            }
            ws.send(json.dumps(payload))
            data = json.loads(ws.recv())
            # print(data)
            stocksBought[symbol]["time"] -= 1
            time.sleep(1)
            order = {
                "topic" : "api:join", 
                "event" : "order", 
                "payload" : {
                "phone_no" : "9971723017", 
                "symbol" : symbol, 
                "buy_sell" : "B", 
                "quantity" : 1, 
                "price" : data["payload"][2]
                }, 
                "ref" : ""
                }
            ws.send(json.dumps(order))
            orderdata = json.loads(ws.recv())
            print(orderdata)
            stocksBought[symbol]["time"] -= 1
            time.sleep(1)
            if(orderdata["payload"]["buy_sell"]=="B"):
                stocksBought[symbol]["buy"] = 1
                stocksBought[symbol]["buyingPrice"] = orderdata["payload"]["price"]
        stocksBought[symbol]["time"] -= 1
        if(stocksBought[symbol]["time"]<=0):
            payload = {
            "topic" : "api:join",
            "event" : "ltp_quote", 
            "payload" : [symbol], 
            "ref" : ""
            }
            ws.send(json.dumps(payload))
            data = json.loads(ws.recv())
            # print(data)
            stocksBought[symbol]["time"] -= 1
            time.sleep(1)
            order = {
                "topic" : "api:join", 
                "event" : "order", 
                "payload" : {
                "phone_no" : "9971723017", 
                "symbol" : symbol, 
                "buy_sell" : "S", 
                "quantity" : 1, 
                "price" : data["payload"][2]
                }, 
                "ref" : ""
                }
            ws.send(json.dumps(order))
            orderdata = json.loads(ws.recv())
            print(orderdata)
            stocksBought[symbol]["time"] -= 1
            time.sleep(1)
            if(orderdata["payload"]["buy_sell"]=="S"):
                profit += orderdata["payload"]["price"] - stocksBought[symbol]["buyingPrice"]
                stocksBought[symbol]["buy"] = 0
                stocksBought[symbol]["time"] = 300

    print(profit/100)
    time.sleep(1)
