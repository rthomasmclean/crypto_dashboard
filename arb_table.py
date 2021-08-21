import pandas as pd
import numpy as np

class table:
    def __init__(self):
        self.dict = {}
        
    def update_table(self, name, exchange, borrow, deposit):
        data = [exchange, borrow, deposit]
        cols = ["Exchange", "Cost to Borrow", 'Yield']
        entry = pd.DataFrame([data], columns=cols)
        if (name in self.dict.keys() and 
            self.dict[name][self.dict[name]["Exchange"] == exchange].empty):
            entry = pd.DataFrame([data], columns=cols)
            self.dict[name] = self.dict[name].append(entry, ignore_index=True)
        elif (name in self.dict.keys() and 
            (self.dict[name][self.dict[name]["Exchange"] == exchange].empty == False)):
            index = self.dict[name].index[self.dict[name]["Exchange"] == exchange]
            self.dict[name].loc[index] = data
        else:
            self.dict[name] = entry
    
    def print_table(self):
        print(self.dict)

    def best_spread(self):
        spreads = {}
        for key in self.dict.keys():
            max_yield = self.dict[key]["Yield"].max()
            max_exchange = self.dict[key]["Exchange"][self.dict[key]["Yield"] == max_yield].values
            if (len(max_exchange) > 0):
                max_exchange = max_exchange[0]
            else:
                max_exchange = np.nan
            min_cost = self.dict[key]["Cost to Borrow"].min()
            min_exchange = self.dict[key]["Exchange"][self.dict[key]["Cost to Borrow"] == min_cost].values
            if (len(min_exchange) > 0):
                min_exchange = min_exchange[0]
            else:
                min_exchange = np.nan
            cols = ["Max Yield", "Max Yield Exchange", "Min Cost", "Min Cost Exchange"]
            data = [max_yield, max_exchange, min_cost, min_exchange]
            spreads[key] = pd.DataFrame([data], columns=cols)
        return spreads