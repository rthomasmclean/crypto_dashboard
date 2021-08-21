import arb_table

import time
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

PATH = "/Users/reedthomas-mclean/Documents/chromedriver"
op = webdriver.ChromeOptions()
op.add_argument("headless")

table = arb_table.table()

def get_body(url):
    driver = webdriver.Chrome(PATH, options=op)
    driver.get(url)
    time.sleep(2)
    get_source = driver.page_source
    parser = BeautifulSoup(get_source, "lxml")
    driver.close()
    body = parser.body
    return body

def launch_aave():
    body = get_body("https://aave.com/")
    table_content_inner = body.select(".Table__content-inner")[0]
    assets = table_content_inner.select(".TableItem__wrapper")
    for a in assets:
        name = a.select(".TableItem__column")[0].find("img", alt=True)["alt"]
        deposit_col = a.select(".TableItem__column")[3]
        deposit_col = deposit_col.select(".APRValue")
        if len(deposit_col) > 0:
            deposit_yield = float(deposit_col[0].text.replace(" %", ""))
        else:
            deposit_yield = np.nan
        borrow_col = a.select(".TableItem__column")[4]
        borrow_col = borrow_col.select(".APRValue")
        if len(borrow_col) > 0:
            borrow_cost = float(borrow_col[0].text.replace(" %", ""))
        else:
            borrow_cost = np.nan
        table.update_table(name, "Aave", borrow_cost, deposit_yield)

def launch_compound():
    body = get_body("https://compound.finance/markets")
    assets = body.select(".asset")
    for a in assets:
        name = a.select(".symbol")[0].text
        data_cols = a.select("div.col-xs-3")
        deposit_yield = float(data_cols[1].find("div").text.replace("%", ""))
        borrow_cost = float(data_cols[3].find("div").text.replace("%", ""))
        table.update_table(name, "Compound", borrow_cost, deposit_yield)

def launch_solfarm():
    body = get_body("https://solfarm.io/lend")
    assets = body.select(".lend-table__row ")
    for a in assets:
        name = a.select(".lend-table__row-item__asset__text")[0].text
        data_cols = a.select(".lend-table__row-item__cell")
        deposit_yield = float(data_cols[2].find("span").text.replace("%", ""))
        borrow_cost = np.nan
        table.update_table(name, "Solfarm", borrow_cost, deposit_yield)

def launch_mangomarkets():
    body = get_body("https://trade.mango.markets/stats")
    assets = body.select("tbody")[0].select("tr")
    for a in assets:
        cols = a.select("td")
        name = cols[0].select(".flex")[0].text
        deposit_yield = float(cols[3].text.replace("Deposit Interest", "").replace("%", ""))
        borrow_cost = float(cols[4].text.replace("Borrow Interest", "").replace("%", ""))
        table.update_table(name, "Mango Markets", borrow_cost, deposit_yield)

def get_dict():
    return table.dict

def get_spreads():
    return table.best_spread()