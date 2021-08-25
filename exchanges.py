import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import time

import arb_table

# PATH references where chromedriver is saved on PC
PATH = "/Users/reedthomas-mclean/Documents/chromedriver"
op = webdriver.ChromeOptions()
# "headless" argument runs Selenium driver without UI
op.add_argument("headless")
op.add_argument("window-size=1920,1080") # Needed for `click()`

table = arb_table.table()

def get_body(url, num):
    driver = webdriver.Chrome(PATH, options=op)
    driver.get(url)
    # Builds in lag to allow slower webpages to load before scraping occurs
    time.sleep(num)
    get_source = driver.page_source
    parser = BeautifulSoup(get_source, "lxml")
    driver.close()
    body = parser.body
    return body

# Functions as `get_body` but accounts for websites that require manual click
def get_body_expand(url, num, button_class):
    driver = webdriver.Chrome(PATH, options=op)
    driver.get(url)
    # Builds in lag to allow slower webpages to load before scraping occurs
    time.sleep(num)
    buttons = driver.find_elements_by_class_name(button_class)
    # Expands the data that is visible to driver
    for b in buttons:
        b.click()
    get_source = driver.page_source 
    parser = BeautifulSoup(get_source, "lxml")
    driver.close()
    body = parser.body
    return body

def launch_aave():
    body = get_body("https://aave.com/", 2)
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
    body = get_body("https://compound.finance/markets", 2)
    assets = body.select(".asset")
    for a in assets:
        name = a.select(".symbol")[0].text
        data_cols = a.select("div.col-xs-3")
        deposit_yield = float(data_cols[1].find("div").text.replace("%", ""))
        borrow_cost = float(data_cols[3].find("div").text.replace("%", ""))
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

def launch_cream():
    # Longer sleep time due to slow loading web page for C.R.E.A.M.
    body = get_body_expand("https://app.cream.finance", 5, "sc-fIoroj")
    borrow_assets = body.select(".rdt_TableBody")
    borrow_assets = body.select(".rdt_TableBody")[1]
    borrow_assets = borrow_assets.select(".rdt_TableRow")
    deposit_assets = body.select(".rdt_TableBody")[0]
    deposit_assets = deposit_assets.select(".rdt_TableRow")
    # Loop accounts for separate borrow and lend tables on website
    for a, b in zip(borrow_assets, deposit_assets):
        data_cols1 = a.select(".sc-eCImvq")
        name = data_cols1[0].select(".sc-jlRMkV.ksCOFC")[0].text
        borrow_cost = data_cols1[1].text
        borrow_cost = float(borrow_cost.replace("%", ""))
        data_cols2 = b.select(".sc-eCImvq")
        deposit_yield = data_cols2[1].text
        deposit_yield = float(deposit_yield.replace("%", ""))
        table.update_table(name, "C.R.E.A.M.", borrow_cost, deposit_yield)

def launch_vesper():
    body = get_body("https://app.vesper.finance/", 2)
    assets = body.select("tbody")[0]
    assets = assets.select("tbody")
    for a in assets:
        name = a.select(".pl-2.align-middle.text-sm")[0].text
        deposit_yield = a.select("div.flex.justify-end.text-xs.font-bold")[0].text.split("+")[0]
        deposit_yield = float(deposit_yield.split()[1].replace("%", ""))
        borrow_cost = np.nan
        table.update_table(name, "Vesper", borrow_cost, deposit_yield)

def launch_88mph():
    # Longer sleep time due to slow loading web page for C.R.E.A.M.
    body = get_body("https://88mph.app", 3)
    assets = body.select("tbody.list")[0]
    assets = assets.select("tr")
    for a in assets:
        name = a.select("td")[0].select(".font-weight-normal.mb-1")[0].text
        deposit_yield = float(a.select("td")[3].text.replace("%", ""))
        borrow_cost = np.nan
        table.update_table(name, "88mph", borrow_cost, deposit_yield)

def launch_solend():
    body = get_body("https://solend.fi/dashboard", 2)
    assets = body.select("tbody.ant-table-tbody")[0]
    assets = assets.select("tr.ant-table-row")
    for a in assets:
        data_cols = a.select("td.ant-table-cell")
        name = data_cols[0].select(".Typography_secondary__2P2Em")[0].text
        borrow_cost = float(data_cols[5].text.replace("%", ""))
        deposit_yield = float(data_cols[3].text.replace("%", ""))
        table.update_table(name, "Soldend", borrow_cost, deposit_yield)
        
def get_dict():
    return table.dict

def get_spreads():
    return table.best_spread()