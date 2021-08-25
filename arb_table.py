import pandas as pd
import numpy as np

class table:
    def __init__(self):
        self.dict = {}
        
    def update_table(self, name, exchange, borrow, deposit):
        data = [exchange, borrow, deposit]
        cols = ["Exchange", "Cost to Borrow", "Yield"]
        entry = pd.DataFrame([data], columns=cols)
        # Append data when the seeing exchange for first time in a non-empty key
        if (name in self.dict.keys() and 
            self.dict[name][self.dict[name]["Exchange"] == exchange].empty):
            entry = pd.DataFrame([data], columns=cols)
            self.dict[name] = self.dict[name].append(entry, ignore_index=True)
        # Replace data when exchange is already in key
        elif (name in self.dict.keys() and 
            (self.dict[name][self.dict[name]["Exchange"] == exchange].empty == False)):
            index = self.dict[name].index[self.dict[name]["Exchange"] == exchange]
            self.dict[name].loc[index] = data
        # First row in previously empty DataFrame
        else:
            self.dict[name] = entry
    
    def print_table(self):
        print(self.dict)

    # Identifies highest returning assets and cheapest to borrow
    def best_spread(self):
        spreads = {}
        for key in self.dict.keys():
            max_yield = self.dict[key]["Yield"].max()
            max_exchange = self.dict[key]["Exchange"][self.dict[key]["Yield"] == max_yield].values
            # Ensure that value exists to avoid "list index out of range error" 
            if (len(max_exchange) > 0):
                max_exchange = max_exchange[0]
            else:
                max_exchange = ""
            min_cost = self.dict[key]["Cost to Borrow"].min()
            min_exchange = self.dict[key]["Exchange"][self.dict[key]["Cost to Borrow"] == min_cost].values
            # Ensure that value exists to avoid "list index out of range error"
            if (len(min_exchange) > 0):
                min_exchange = min_exchange[0]
            else:
                min_exchange = ""
            cols = ["Max Yield", "Max Yield Exchange", "Min Cost", "Min Cost Exchange", "Spread", "Color"]
            spread = "-"
            color = ""
            if (np.isnan(max_yield) == False):
                if (np.isnan(min_cost) == False):
                    spread = max_yield - min_cost
                    # Color variable used to color code "Spread" column
                    if (spread > 0):
                        color = "G"
                    if (spread < 0):
                        color = "R"
                    spread = "{:.2f}%".format(spread)
                max_yield = "{:.2f}%".format(max_yield)
            else:
                max_yield = "-"
            if (np.isnan(min_cost) == False):
                min_cost = "{:.2f}%".format(min_cost)
            else: 
                min_cost = "-"
            data = [max_yield, max_exchange, min_cost, min_exchange, spread, color]
            spreads[key] = pd.DataFrame([data], columns=cols)
        return spreads