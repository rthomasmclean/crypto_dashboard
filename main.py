from flask import Flask, render_template
import exchanges
import time

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("test.html", assets=exchanges.get_dict().keys(), data=exchanges.get_spreads())

def launch_drivers():
    # exchanges.launch_aave()
    # exchanges.launch_compound()
    # exchanges.launch_solfarm()
    exchanges.launch_mangomarkets()

def main():
    launch_drivers()
    # print(exchanges.get_spreads())

if __name__ == "__main__":
    main()
    app.run()
