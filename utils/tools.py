import json
import requests
import pandas as pd
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
from utils.key import key, key2

from datetime import datetime
# Event handling
epoch = datetime(1970, 1, 1)
p = '%Y-%m-%dT%H:%M:%S.%f'
p2 = '%Y-%m-%dT%H:%M:%S'

def to_epoch_time(t):
    try:
        return (datetime.strptime(t, p) - epoch).total_seconds()
    except:
        return (datetime.strptime(t, p2) - epoch).total_seconds()
##################################################################
####################### Read data from url #######################
##################################################################
# Requests
headers1 = {"Accept": "application/json", "X-API-KEY" : key}
headers2 = {"Accept": "application/json", "X-API-KEY" : key2}
base_url = "https://api.opensea.io/api/v1/events?"
sales_url = "https://api.opensea.io/api/v1/events?event_type=successful"
listing_url = "https://api.opensea.io/api/v1/events?event_type=created"

def get_data_with_url(url, headers=headers1):
    try:
        sleep(0.25)
        return json.loads(requests.request("GET", url, headers=headers).text)
    except Exception as e:
        r = requests.request("GET", url, headers=headers)
        print(e, r.status_code, url)

def get_stats(slug):
    url = "https://api.opensea.io/api/v1/collection/" + slug
    response = requests.request("GET", url)
    data = json.loads(response.text)["collection"]
    #print(data.keys())
    #print(data)
    # floor, one_day_volume, total_volume, total_supply, num_owners
    #sell_fee, external_url
    #'twitter_username', 'instagram_username'
    return data["stats"]["floor_price"], round(data["stats"]["one_day_volume"], 2), round(data["stats"]["total_volume"], 2), int(data["stats"]["total_supply"]), data["stats"]["num_owners"], float(data["dev_seller_fee_basis_points"]) / 100, data["external_url"], data["discord_url"], data["twitter_username"], data["instagram_username"]

def get_last_sellers_buyers(slug):
    data = get_data_with_url("https://api.opensea.io/api/v1/events?collection_slug={}&event_type=successful".format(slug), headers=headers2)
    if len(data["asset_events"]) == 0:
        return 0, 0, 0
    df = pd.DataFrame(data["asset_events"])
    wa = df["winner_account"].apply(lambda x : x["address"]).unique()
    sa = df["seller"].apply(lambda x : x["address"]).unique()
    # Plot last sales
    df["total_price_"] = df.total_price.astype(float) / 1e18
    df["event_timestamp_"] = pd.to_datetime(df["event_timestamp"])

    q1, q2 = df.total_price_.quantile([0.25, 0.75])
    df = df[(df.total_price_ >= q1) & (df.total_price_ <= q2)]

    plt.figure(figsize=(8, 6))
    lines = plt.plot(df["event_timestamp_"], df["total_price_"], alpha=0.6)
    plt.scatter(df["event_timestamp_"], df["total_price_"], alpha=0.6)
    data = lines[0].get_xydata()
    x = data[:, 0]
    y = data[:, 1]
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m*x+b, '--k')
    plt.title("Last sales")
    plt.ylabel("price")
    plt.xlabel("Timestamp")
    plt.savefig("data/online/sales/{}.png".format(slug))
    plt.close()
    return len(wa), len(sa), len(df), m * x[0] + b
