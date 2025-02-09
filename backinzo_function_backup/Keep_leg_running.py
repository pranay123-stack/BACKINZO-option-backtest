import pandas as pd
from datetime import datetime


def round_to_nearest_hundred(value):
    # Divide the value by 100 and separate it into whole number and remainder
    quotient, remainder = divmod(value, 100)
    
    # If remainder is less than 50, round down; if 50 or more, round up
    if remainder < 50:
        return quotient * 100
    else:
        return (quotient + 1) * 100

def atm_row_at_time_t(df,start_time):
    atm_row = df[df['Time'] == start_time]
    return atm_row

def strike_price_row_at_time_t(df,atm_row,start_time):
    return int(round_to_nearest_hundred(atm_row.iloc[0]['ATM_Close']))

def ohlc_row_at_time_t(df, ticker_row_at_time):
    if ticker_row_at_time.empty:
        return None  # Or some other indication that no data was found
    return ticker_row_at_time.iloc[0]['Close']

def  ticker_row_at_time(df,symbol_to_search, time):
    return  df[(df['Ticker'] ==symbol_to_search) & (df['Time'] == time)]


def straddle_backtest(csv_file_path, start_time,squareoff_time, legs):

    df = pd.read_csv(csv_file_path)
    
    atm_row = atm_row_at_time_t(df,start_time)
    trades_df = pd.DataFrame(columns=['Symbol', 'EntryTime', 'EntryPrice','EntryType','ExitTime','ExitPrice'])
    exit_time = None
    for leg in legs:
        
        symbol_to_search = f"{leg['Symbol']}{strike_price_row_at_time_t(df,atm_row,start_time)+leg['offset'] }{leg['type']}.NFO"
        ticker_row_entry = ticker_row_at_time(df,symbol_to_search, start_time)
        # ticker_row_exit = ticker_row_at_time(df,symbol_to_search, squareoff_time)
        entry_price = ohlc_row_at_time_t(df, ticker_row_entry)
        exit_price = entry_price * 1.5





        # Only filter df within this scope, do not overwrite df
        filtered_df = df[(df['Time'] > start_time) & (df['Time'] < squareoff_time)]
        filtered_df = filtered_df[filtered_df['Ticker'] == symbol_to_search]
        exit_row = filtered_df[filtered_df['High'] >= exit_price]  # Check for the condition within filtered_df












      
        ticker_row_exit = ticker_row_at_time(df, symbol_to_search, squareoff_time)
        exit_price = ohlc_row_at_time_t(df, ticker_row_exit)
        exit_time = squareoff_time 


        







        # Create a new DataFrame for the row you want to add
        new_row = pd.DataFrame({
            'Symbol': [symbol_to_search],
            'EntryTime': [start_time],
            'EntryPrice': [entry_price],
            'EntryType':leg['EntryType'],
            'ExitPrice': [exit_price],
            'ExitTime': [exit_time],
      
            
       
        })

        # Use concat to append the new row to trades_df
        trades_df = pd.concat([trades_df, new_row], ignore_index=True)
        trades_df.to_csv('/Users/pranaygaurav/Downloads/AlgoTrading/KREDENT_TRADING/backinzo/trade_results.csv', index=False)
    return trades_df





csv_file_path = '/Users/pranaygaurav/Downloads/AlgoTrading/KREDENT_TRADING/backinzo/atm_option.csv'
start_time = "09:19:59"
squareoff_time = "15:24:59"
legs = [
    {'Symbol':'BANKNIFTY06MAR24','type': 'CE','EntryType':"Sell",'ExitType':"Buy" ,'lot_size': 15,'offset':0  },   
    {'Symbol':'BANKNIFTY06MAR24','type': 'PE','EntryType':"Sell",'ExitType':"Buy", 'lot_size': 15,'offset':0  },  
  
]

# Execute the multi-leg straddle backtest
result = straddle_backtest(csv_file_path, start_time,squareoff_time, legs)
print(result)
