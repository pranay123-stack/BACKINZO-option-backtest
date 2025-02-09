import pandas as pd
from datetime import datetime

# Global configuration
backtest_config = {
    "entry_csv_file_path": "/Users/pranaygaurav/Downloads/AlgoTrading/Harshul Daga_FNO+IDX/BACKTEST_ATM/ATM_BANKNIFTY/MAR/ATM_BANKNIFTY_01MAR24.csv",
    "trades_df_csv_path" : "/Users/pranaygaurav/Downloads/AlgoTrading/Harshul Daga_FNO+IDX/BACKTEST_ATM/ATM_BANKNIFTY/MAR/trades_df.csv",
    "entry_time": "09:19:59",
    "squareoff_time": "15:24:59",
    "stoploss_percentage": 50,
    "target_percentage": 50,
    "Underlying_Symbol":"",
    "wait_time_before_next_rentry":5,
    "entrylegs_details": [
    {'id': 1, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 600, "reexecute_count": 1 },
    {'id': 2, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': -500, "reexecute_count": 1,},


    ]
  
}





def extract_symbol_and_expiry(ticker):
    import re
    match = re.match(r'([A-Z]+)(\d{2}[A-Z]{3}\d{2})', ticker)
    if match:
        symbol = match.group(1)
        backtest_config['Underlying_Symbol'] = symbol
        expiry = match.group(2)
        return symbol + expiry, symbol
    return None, None

def update_entrylegs_details(csv_file_path, entrylegs_details):
    df = pd.read_csv(csv_file_path)
    if not df.empty:
        sample_ticker = df.iloc[0]['Ticker']
        symbol_expiry, symbol = extract_symbol_and_expiry(sample_ticker)
        if symbol_expiry and symbol:
            for leg in entrylegs_details:
                leg['Ticker_Symbol'] = symbol_expiry
                if symbol == 'NIFTY':
                    leg['lot_size'] = 50
                elif symbol == 'BANKNIFTY':
                    leg['lot_size'] = 15
    return entrylegs_details

def atm_at_time_t(df,start_time,symbol):
    atm_row = df[df['Time'] == start_time]
    atm =0


    if symbol == 'NIFTY':
        atm= int(round(atm_row.iloc[0]['ATM_close'] / 50) * 100)
           
    elif symbol == 'BANKNIFTY':
        atm= int(round(atm_row.iloc[0]['ATM_close'] / 100) * 100)
  
    return atm

def  ticker_row_at_time(df,symbol_to_search, time):
    return  df[(df['Ticker'] ==symbol_to_search) & (df['Time'] == time)]

def get_ohlc_ticker_row_at_time_t(df, ticker_row_at_time,ohlc_column):
    if ticker_row_at_time.empty:
        return None  # Or some other indication that no data was found

    if ohlc_column == 'High':
       return ticker_row_at_time.iloc[0]['High']
    elif ohlc_column == 'Low':
        return ticker_row_at_time.iloc[0]['Low']
    elif ohlc_column == 'Close':
        return ticker_row_at_time.iloc[0]['Close']
    elif ohlc_column == 'Open':
        return ticker_row_at_time.iloc[0]['Open']
    else:
        return None

def place_order_at_atm_price(df,symbol, leg, entry_time):


    atm = atm_at_time_t(df,entry_time,symbol)
    print("ATM VALUE ===",atm)
    strike = atm+ leg['offset']
    print("strike ===",strike)
   

   
    symbol_to_search = f"{leg['Ticker_Symbol']}{strike}{leg['type']}.NFO"

    
    print("symbol_to_search ===",symbol_to_search)
    ticker_row_entry = ticker_row_at_time(df, symbol_to_search, entry_time)
    print("ticker_row_entry ===",ticker_row_entry)
    entry_price =  get_ohlc_ticker_row_at_time_t(df,  ticker_row_entry ,"Close")
    print("entry_price ===",entry_price)
    
    sl_multiplier = 1+(backtest_config['stoploss_percentage'] /100)
    sl_hit_price = entry_price * sl_multiplier 
    print("sl_hit_price ===",sl_hit_price)



    tl_multiplier = backtest_config['target_percentage'] / 100
    value = entry_price * tl_multiplier
    target_price = entry_price - value
    print("target_price ===",target_price)
  
    
  
    
    return {
        'symbol_to_search': symbol_to_search,
        'Entry_type':"sell",
        'Entry_time': entry_time,
        'Entry_price': entry_price,
        'sl_hit_price': sl_hit_price,
        'target_price': target_price
    }


def take_reentry(df,symbol, trades_df, pending_legs, leg, reentry_entry_time,squareoff_time):
    while leg['reexecute_count'] > 0:
        entry_order_details = place_order_at_atm_price(df,symbol, leg, reentry_entry_time)
        exit_row =  exit_check(df,entry_order_details,squareoff_time)

        if exit_row is not None:
            exit_price = exit_row['Close']
            exit_time = exit_row['Time']
            exit_type = "Buy"

            trade_details = {
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['Entry_time'],
                'EntryPrice': entry_order_details['Entry_price'],
                'EntryType': entry_order_details['Entry_type'],
                'ExitTime': exit_time,
                'ExitPrice': exit_price,
                'ExitType': exit_type
            }
            trades_df = append_trade_to_df(trades_df,  trade_details)
            leg['reexecute_count'] -= 1
        else:
            if leg not in [p['leg'] for p in pending_legs]:
                pending_legs.append({'leg': leg, 'entry_order_details':entry_order_details})
            break
    return trades_df, pending_legs

def handle_pending_legs(df, trades_df, pending_legs, squareoff_time):
    for pendingleg in pending_legs:
        leg = pendingleg['leg']
        entry_order_details = pendingleg['entry_order_details']
        symbol_to_search = entry_order_details['symbol_to_search']
        ticker_row_exit = ticker_row_at_time(df, symbol_to_search, squareoff_time)
        exit_price = get_ohlc_ticker_row_at_time_t(df, ticker_row_exit,"Close")
        exit_time = squareoff_time 
        exit_type = 'Buy'

        trade_details = {
            'Symbol': symbol_to_search,
            'EntryTime': entry_order_details['Entry_time'],  # This assumes entry_time is properly stored in leg
            'EntryPrice': entry_order_details['Entry_price'],  # Likewise for entry_price
            'EntryType': entry_order_details['Entry_type'],
            'ExitTime': exit_time,
            'ExitPrice': exit_price,
            'ExitType': exit_type
        }
        trades_df = append_trade_to_df(trades_df, trade_details)

    return trades_df

def append_trade_to_df(trades_df,trade_details ):
  
    new_row = pd.DataFrame([trade_details])
    return pd.concat([trades_df, new_row], ignore_index=True)
    
def exit_check(df, entry_order_details,squareoff_time):
    entry_symbol = entry_order_details['symbol_to_search']
    entry_time = entry_order_details['Entry_time']
    entry_target = entry_order_details['target_price']
    entry_stoploss = entry_order_details['sl_hit_price']
 

    filtered_df = df[(df['Time'] > entry_time) & (df['Time'] <= squareoff_time) & (df['Ticker'] == entry_symbol)]
    sl_filter = filtered_df[(filtered_df['High'] >= entry_stoploss)]
    target_filter = filtered_df[(filtered_df['Low'] <= entry_target)]

    # Find the first row where 'High' is greater than or equal to the exit price
    exit_row = target_filter

    if not exit_row.empty:
        return exit_row.iloc[0]  # Return the first row meeting the condition
    else:
        return None  # Return None if no row meets the condition


          
          

    

   
 
        


            


def reexecute(csv_file_path,symbol, entry_time,squareoff_time, legs):
    df = pd.read_csv(csv_file_path)
    trades_df =pd.DataFrame(columns=['Symbol', 'EntryTime', 'EntryPrice','EntryType','ExitTime','ExitPrice', 'ExitType'])
    pending_legs = []
    exit_time = None

   
    for leg in legs:
        entry_order_details = place_order_at_atm_price(df,symbol, leg, entry_time)
        symbol_to_search = entry_order_details['symbol_to_search']
        exit_row = exit_check(df,entry_order_details,squareoff_time)


        if exit_row is not None and not exit_row.empty: 
            exit_price = exit_row['Close']
            exit_time = exit_row['Time']
            exit_type = "buy"
            reentry_entry_time = exit_time
            trade_details = {
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['Entry_time'],
                'EntryPrice': entry_order_details['Entry_price'],
                'EntryType': entry_order_details['Entry_type'],
                'ExitTime': exit_time,
                'ExitPrice': exit_price,
                'ExitType': exit_type
            }
            trades_df = append_trade_to_df(trades_df,  trade_details)
          
            trades_df, pending_legs = take_reentry(df,symbol, trades_df, pending_legs, leg,reentry_entry_time,squareoff_time)
        
        else:
            ticker_row_exit = ticker_row_at_time(df, symbol_to_search, squareoff_time)
            exit_price =  get_ohlc_ticker_row_at_time_t(df, ticker_row_exit,"Close")
            exit_time = squareoff_time 
            trade_details = {
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['Entry_time'],
                'EntryPrice': entry_order_details['Entry_price'],
                'EntryType': entry_order_details['Entry_type'],
                'ExitTime': exit_time,
                'ExitPrice': exit_price,
                'ExitType': "buy"
            }
            trades_df = append_trade_to_df(trades_df,  trade_details)
       
    handle_pending_legs(df, trades_df , pending_legs , squareoff_time)
    trades_df.to_csv(backtest_config['trades_df_csv_path'], index=False)
    return trades_df





entrylegs_details = update_entrylegs_details(backtest_config['entry_csv_file_path'], backtest_config['entrylegs_details'])


#Execute the multi-leg straddle backtest
result = reexecute(backtest_config['entry_csv_file_path'],backtest_config['Underlying_Symbol'],backtest_config['entry_time'],backtest_config['squareoff_time'], backtest_config['entrylegs_details'])
print(result)








