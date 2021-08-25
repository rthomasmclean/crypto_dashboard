from flask import Flask, render_template, jsonify
import exchanges

app = Flask(__name__)

# URLs used as links in dashboard
exchange_urls = {
    "Aave": "https://aave.com",
    "Compound": "https://compound.finance/markets",
    "Solfarm": "https://solfarm.io/lend",
    "Mango Markets": "https://trade.mango.markets/stats",
    "C.R.E.A.M.": "https://app.cream.finance",
    "Vesper": "https://vesper.finance",
    "88mph": "https://88mph.app",
    "Solend": "https://solend.fi/dashboard"
}

# Called every [x] milliseconds in order to refresh data in dashboard
@app.route("/update_dashboard", methods=["POST"])
def updatedash():
    launch_drivers()
    # Spreads are updated based on the refreshed data generated from `launch_drivers`
    spreads = exchanges.get_spreads()
    return jsonify("", render_template("update_dash.html", assets=exchanges.get_dict().keys(), data=spreads, urls=exchange_urls))

@app.route("/")
def home():
    return render_template("dash.html", assets=exchanges.get_dict().keys(), data=exchanges.get_spreads(), urls=exchange_urls)

# The following functions scrape relevant data from these platforms
def launch_drivers():
    exchanges.launch_aave()
    exchanges.launch_compound()
    exchanges.launch_solfarm()
    exchanges.launch_mangomarkets()
    exchanges.launch_cream()
    exchanges.launch_vesper()
    exchanges.launch_88mph()
    exchanges.launch_solend()

launch_drivers()
app.run()
