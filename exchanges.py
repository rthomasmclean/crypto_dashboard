import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import requests

import arb_table

# PATH references where chromedriver is saved on PC
PATH = "/Users/reedthomas-mclean/Documents/chromedriver"
op = webdriver.ChromeOptions()
# "headless" argument runs Selenium driver without UI
op.add_argument("headless")

table = arb_table.table()

# Scrapes data from protocols that lack sufficient APIs
def get_body(url, num):
    driver = webdriver.Chrome(PATH, options=op)
    driver.get(url)
    # Builds in lag to allow slower webpages to load before scraping
    time.sleep(num)
    get_source = driver.page_source
    parser = BeautifulSoup(get_source, "lxml")
    driver.close()
    body = parser.body
    return body

# Access using query on subgraph
def launch_aave():
    query = '''
    {
    reserves {
        symbol
        liquidityRate 
        variableBorrowRate
    }
    }
    '''
    RAY = 10**27

    request = requests.post("https://api.thegraph.com/subgraphs/name/aave/protocol-v2", 
                            json={'query': query})
    json_data = request.json()
    assets = json_data["data"]["reserves"]
    for a in assets:
        name = a["symbol"]
        borrow_cost = 100 * int(a["variableBorrowRate"])/RAY
        deposit_yield = 100 * int(a["liquidityRate"])/RAY    
        table.update_table(name, "Aave", borrow_cost, deposit_yield)

# Access using Compound API
def launch_compound():
    response = requests.get("https://api.compound.finance/api/v2/ctoken")
    json_data = response.json()
    json_data = json_data["cToken"]
    for a in json_data:
        name = a["underlying_symbol"]
        borrow_cost = float(a["borrow_rate"]["value"]) * 100
        deposit_yield = float(a["supply_rate"]["value"]) * 100
        table.update_table(name, "Compound", borrow_cost, deposit_yield)

def launch_solfarm():
    body = get_body("https://solfarm.io/lend", 2)
    assets = body.select(".lend-table__row ")
    for a in assets:
        name = a.select(".lend-table__row-item__asset__text")[0].text
        data_cols = a.select(".lend-table__row-item__cell")
        deposit_yield = float(data_cols[2].find("span").text.replace("%", ""))
        borrow_cost = np.nan
        table.update_table(name, "Solfarm", borrow_cost, deposit_yield)

def launch_mangomarkets():
    body = get_body("https://trade.mango.markets/stats", 2)
    assets = body.select("tbody")[0].select("tr")
    for a in assets:
        cols = a.select("td")
        name = cols[0].select(".flex")[0].text
        deposit_yield = float(cols[3].text.replace("Deposit Interest", "").replace("%", ""))
        borrow_cost = float(cols[4].text.replace("Borrow Interest", "").replace("%", ""))
        table.update_table(name, "Mango Markets", borrow_cost, deposit_yield)

# Access using C.R.E.A.M. API
def launch_cream():
    response = requests.get("https://api.cream.finance/api/v1/rates?comptroller=eth")
    json_data = response.json()
    borrow_assets = json_data["borrowRates"]
    deposit_assets = json_data["lendRates"]
    for a, b in zip(borrow_assets, deposit_assets):
        name = a["tokenSymbol"]
        if name == "FTX Token":
            name = "FTT"
        borrow_cost = float(a["apy"]) * 100
        deposit_yield = float(b["apy"]) * 100
        table.update_table(name, "C.R.E.A.M.", borrow_cost, deposit_yield)

# Access using Vesper API
def launch_vesper():
    response = requests.get("https://api.vesper.finance/loan-rates")
    json_data = response.json()
    assets = json_data["lendRates"]
    for a in assets:
        name = a["tokenSymbol"]
        deposit_yield = float(a["apy"]) * 100
        borrow_cost = np.nan
        table.update_table(name, "Vesper", borrow_cost, deposit_yield)

# Access using 88mph API
def launch_88mph():
    response = requests.get("https://api.88mph.app/pools")
    assets = response.json()
    for a in assets:
        name = a["tokenSymbol"]
        deposit_yield = float(a["mphAPY"])
        borrow_cost = np.nan
        table.update_table(name, "88mph", borrow_cost, deposit_yield)

def launch_solend():
    symbol_map = {
        "Solana": "SOL",
        "USDC": "USDC",
        "Ethereum": "ETH",
        "Bitcoin": "BTC",
        "Serum": "SRM",
        "USDT": "USDT",
        "FTT": "FTT",
        "Raydium": "RAY"
    }
    body = get_body("https://solend.fi/dashboard", 2)
    assets = body.select("tbody.ant-table-tbody")[0]
    assets = assets.select("tr.ant-table-row")
    for a in assets:
        data_cols = a.select("td.ant-table-cell")
        name = symbol_map[data_cols[0].select(".Typography_primary__r-t61")[0].text]
        borrow_cost = float(data_cols[5].text.replace("%", ""))
        deposit_yield = float(data_cols[3].text.replace("%", ""))
        table.update_table(name, "Soldend", borrow_cost, deposit_yield)

# Access using Fulcrum API
def launch_fulcrum():
    response1 = requests.get("https://api.bzx.network/v1/supply-rate-apr?networks=eth")
    response2 = requests.get("https://api.bzx.network/v1/borrow-rate-apr?networks=eth")
    borrow_assets = response2.json()
    borrow_assets = borrow_assets["data"]["eth"]
    deposit_assets = response1.json()
    deposit_assets = deposit_assets["data"]["eth"]
    for a, b in zip(borrow_assets.keys(), deposit_assets.keys()):
        name = a.upper()
        borrow_cost = float(borrow_assets[a])
        deposit_yield = float(deposit_assets[b])
        table.update_table(name, "Fulcrum", borrow_cost, deposit_yield)
        
def get_dict():
    return table.dict

def get_spreads():
    return table.best_spread()