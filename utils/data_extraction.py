import requests
import json
import pickle
import os
import pandas as pd
import time
from datetime import datetime
from utils.key import key
sales_path = "data/sales/"

deal_event_elem = {
    "successful" : lambda x: [x["event_type"],
                              x["auction_type"],
                              int(x["asset"]["token_id"]),
                              float(x["total_price"]) / basis,
                              x["created_date"],
                              x["duration"]],
    "created" : lambda x: [x["event_type"],
                           x["auction_type"],
                           int(x["asset"]["token_id"]),
                           float(x["starting_price"]) / basis,
                           x["created_date"],
                           x["duration"]],
}
before_time_ = 1653696000 # Saturday 05 28 2022 00:00:00 GMT
before_time_ = 1655439642
basis = 1e18
# Headers
headers = {"Accept": "application/json", "X-API-KEY" : key}
base_url = "https://api.opensea.io/api/v1/events?"

def get_events_by_url(url, type_event):
    request_url = url
    events = []
    cursor = ""
    while cursor is not None:
        try:
            response = requests.request("GET", url, headers=headers)
            data = json.loads(response.text)
            for elem in data["asset_events"]:
                try:
                    events.append(deal_event_elem[type_event](elem))
                except:
                    pass # sell as bundle
            cursor = data["next"]
            url = request_url + "&cursor={}".format(cursor)
            time.sleep(0.1)
        except:
            print(response.text, response.status_code)
            print(url, cursor)
            if response.status_code == 429:
                retry_time = int(response.headers["Retry-After"])
                print("Retry in " + str(retry_time) + "seconds")
                time.sleep(retry_time)
    return events


def get_events(address, type_event, token_id = "", before_time=before_time_):
    print(type_event)
    # url conditions
    listed = "event_type=" + type_event
    addr = "asset_contract_address={}".format(address)
    if before_time != before_time_:
        before_time = two_week_after_creation(name)
    before = "occurred_before={}".format(before_time)
    if token_id != "":
        token_id = "token_id=" + str(token_id)
    filters = "&".join([listed,
                        addr,
                        before,
                        token_id,
                       ])
    url = base_url + filters
    print(url)
    events = get_events_by_url(url, type_event)
    return events

def get_name_from_address(addr):
    url = "https://api.opensea.io/api/v1/asset_contract/{}".format(addr)
    data = requests.request("GET", url, headers=headers)
    return json.loads(data.text)["name"]

def get_sales(addr):
    path = sales_path
    elapsed_time = -time.time()
    name = get_name_from_address(addr)
    print(name)
    try:
        df = pd.read_csv(path + name + ".csv")
    except:
        events = []
        for event_type in ["successful", "created"]:
            events += get_events(addr, event_type)
        df = pd.DataFrame(events, 
                          columns=["event", "auction_type", "ID", "price", "timestamp", "duration"]
                         ).sort_values(by="timestamp")
        df.to_csv(path + name + ".csv", index=False)
    elapsed_time += time.time()
    print("Elapsed time {}".format(elapsed_time))
    return df

