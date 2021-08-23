from flask import Flask, render_template, jsonify
import exchanges
import time

app = Flask(__name__)

exchange_urls = {
    "Aave": "https://aave.com",
    "Compound": "https://compound.finance/markets",
    "Solfarm": "https://solfarm.io/lend",
    "Mango Markets": "https://trade.mango.markets/stats"
}

@app.route("/update_dashboard", methods=["POST"])
def updatedash():
    launch_drivers()
    spreads = exchanges.get_spreads()
    return jsonify("", render_template("update_dash.html", assets=exchanges.get_dict().keys(), data=spreads, urls=exchange_urls))

@app.route("/")
def home():
    return render_template("dash.html", assets=exchanges.get_dict().keys(), data=exchanges.get_spreads(), urls=exchange_urls)

def launch_drivers():
    exchanges.launch_aave()
    exchanges.launch_compound()
    exchanges.launch_solfarm()
    exchanges.launch_mangomarkets()


launch_drivers()
app.run()
