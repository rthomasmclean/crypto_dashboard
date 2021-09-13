import numpy as np
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
            price {
                id
                priceInEth
            }
            liquidityRate 
            variableBorrowRate
            decimals
            totalDeposits
        }
        priceOracles {
            usdPriceEth
        }
    }
    '''
    # Aave's API returns data in terms of RAY units to reduce the impact of rounding errors
    RAY = 10**27
    request = requests.post("https://api.thegraph.com/subgraphs/name/aave/protocol-v2", 
                            json={'query': query})
    json_data = request.json()
    assets = json_data["data"]["reserves"]
    usd_eth = json_data["data"]["priceOracles"]
    # Returns current ETH price in USD
    eth_price = int(usd_eth[0]["usdPriceEth"])
    for a in assets:
        name = a["symbol"]
        borrow_cost = 100 * int(a["variableBorrowRate"])/RAY
        deposit_yield = 100 * int(a["liquidityRate"])/RAY 
        total_deposits = int(a["totalDeposits"])
        decimals = int(a["decimals"])
        total_deposits = total_deposits / (10**decimals)
        # Calculate deposits in terms of ETH price
        conversion = eth_price / int(a["price"]["priceInEth"])
        # Convert unit of measure to USD
        tvl = total_deposits / conversion
        table.update_table(name, "Aave", borrow_cost, deposit_yield, tvl)

# Access using Compound API
def launch_compound():
    response = requests.get("https://api.compound.finance/api/v2/ctoken")
    json_data = response.json()
    json_data = json_data["cToken"]
    for a in json_data:
        name = a["underlying_symbol"]
        borrow_cost = float(a["borrow_rate"]["value"]) * 100
        deposit_yield = float(a["supply_rate"]["value"]) * 100
        total_supply = float(a["total_supply"]["value"])
        exchange = float(a["exchange_rate"]["value"])
        price = float(a["underlying_price"]["value"])
        # Measure liquidity in terms of underlying token
        underlying_liquidity = total_supply * exchange
        usd_eth = eth_price_usd()
        # Underlying liquidity converted -> ETH -> USD
        tvl = underlying_liquidity * price * usd_eth
        table.update_table(name, "Compound", borrow_cost, deposit_yield, tvl)

# Scrape data due to no functional API available
def launch_solfarm():
    body = get_body("https://solfarm.io/lend", 2)
    assets = body.select(".lend-table__row ")
    for a in assets:
        name = a.select(".lend-table__row-item__asset__text")[0].text
        data_cols = a.select(".lend-table__row-item__cell")
        deposit_yield = float(data_cols[2].find("span").text.replace("%", ""))
        borrow_cost = np.nan
        tvl = data_cols[3].select(".lend-table__row-item__cell-usd")[0].text
        tvl = tvl.replace("$", "").replace(",","")
        if tvl[-1] == "M":
            tvl = tvl.replace("M", "")
            tvl = float(tvl) * 1000000
        else:
            tvl = float(tvl)
        table.update_table(name, "Solfarm", borrow_cost, deposit_yield, tvl)

# Scrape data due to no functional API available
def launch_mangomarkets():
    body = get_body("https://trade.mango.markets/stats", 3)
    assets = body.select("tbody")[0].select("tr")
    # Update to incorporate future assets added to platform
    API_map = {
        "USDC": "usd-coin",
        "MNGO": "mango-markets",
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "USDT": "tether",
        "SRM": "serum",
    }
    # Coingecko API allows us to convert collateral / liquidity of underlying token to USD
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=usd-coin%2Cmango-markets%2Cbitcoin%2Cethereum%2Csolana%2Ctether%2Cserum&vs_currencies=usd")
    prices = response.json()
    for a in assets:
        cols = a.select("td")
        name = cols[0].select(".flex")[0].text
        deposit_yield = float(cols[3].text.replace("Deposit Interest", "").replace("%", ""))
        borrow_cost = float(cols[4].text.replace("Borrow Interest", "").replace("%", ""))
        tvl = float(cols[1].text.replace(",", ""))
        price_usd = prices[API_map[name]]["usd"]
        tvl = tvl * price_usd
        table.update_table(name, "Mango Markets", borrow_cost, deposit_yield, tvl)

# Access using C.R.E.A.M. API / subgraph query
def launch_cream():
    query = '''
        {
            markets {
                borrowRate
                supplyRate
                underlyingSymbol
                underlyingPriceUSD
                cash
            }
        }
        '''
    response = requests.post("https://api.thegraph.com/subgraphs/name/creamfinancedev/cream-lending", json={"query": query})
    json_data = response.json()
    assets = json_data["data"]["markets"]
    for a in assets:
        name = a["underlyingSymbol"]
        if name == "FTX Token":
            name = "FTT" # for consistency across platforms
        deposit_yield = float(a["supplyRate"]) * 100
        borrow_cost = float(a["borrowRate"]) * 100
        tvl = float(a["cash"]) * float(a["underlyingPriceUSD"]) # Cash is the amount of underlying balance owned by this crToken contract
        table.update_table(name, "C.R.E.A.M.", borrow_cost, deposit_yield, tvl)

# Access using Vesper API
def launch_vesper():
    response_rates = requests.get("https://api.vesper.finance/loan-rates")
    json_data_rates = response_rates.json()
    assets_rates = json_data_rates["lendRates"]
    response_pools = requests.get("https://api.vesper.finance/pools")
    assets_pools = response_pools.json()
    for a, b in zip(assets_rates, assets_pools):
        name = a["tokenSymbol"]
        deposit_yield = float(a["apy"]) * 100
        borrow_cost = np.nan
        price = float(b["asset"]["price"])
        decimals = int(b["asset"]["decimals"])
        liquidity = float(b["totalValue"]) / (10**decimals)
        tvl = liquidity * price
        table.update_table(name, "Vesper", borrow_cost, deposit_yield, tvl)

# Access using 88mph API
def launch_88mph():
    response = requests.get("https://api.88mph.app/pools")
    assets = response.json()
    for a in assets:
        name = a["tokenSymbol"]
        deposit_yield = float(a["mphAPY"])
        borrow_cost = np.nan
        tvl = float(a["totalValueLockedInUSD"])
        table.update_table(name, "88mph", borrow_cost, deposit_yield, tvl)

# Scrape data due to no functional API available
def launch_solend():
    # Map so that assets are compared consistently across platforms
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
        tvl = data_cols[1].select("label.Typography_secondary__2P2Em")[0].text
        tvl = float(tvl.replace("$", "").replace(",", ""))
        table.update_table(name, "Solend", borrow_cost, deposit_yield, tvl)

# Access using Fulcrum API
def launch_fulcrum():
    response1 = requests.get("https://api.bzx.network/v1/supply-rate-apr?networks=eth")
    response2 = requests.get("https://api.bzx.network/v1/borrow-rate-apr?networks=eth")
    response3 = requests.get("https://api.bzx.network/v1/total-asset-supply?networks=eth")
    response4 = requests.get("https://api.bzx.network/v1/oracle-rates-usd?networks=eth")
    borrow_assets = response2.json()
    borrow_assets = borrow_assets["data"]["eth"]
    deposit_assets = response1.json()
    deposit_assets = deposit_assets["data"]["eth"]
    tvl_assets = response3.json()
    tvl_assets = tvl_assets["data"]["eth"]
    asset_prices_usd = response4.json()
    asset_prices_usd = asset_prices_usd["data"]["eth"]
    for a, b, c, d in zip(borrow_assets.keys(), deposit_assets.keys(), tvl_assets.keys(), asset_prices_usd.keys()):
        name = a.upper()
        borrow_cost = float(borrow_assets[a])
        deposit_yield = float(deposit_assets[b])
        tvl = float(tvl_assets[c]) * float(asset_prices_usd[d])
        table.update_table(name, "Fulcrum", borrow_cost, deposit_yield, tvl)
        
def get_dict():
    return table.dict

def get_spreads():
    return table.best_spread()

def eth_price_usd():
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd")
    json_data = response.json()
    usd_eth = json_data["ethereum"]["usd"]
    return float(usd_eth)