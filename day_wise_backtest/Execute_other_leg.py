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
    "entrylegs_details": [
    {'id': 1, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 500, "execute_leg": [2], "execute_now": True},
    {'id': 2, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 0, "execute_leg": [3,4], "execute_now": False},
    {'id': 3, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 200, "execute_leg": [5], "execute_now": False},
    {'id': 4, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': -300, "execute_leg": [6], "execute_now": False},
    {'id': 5, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 100, "execute_leg": [6], "execute_now": False},
    {'id': 6, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': -100, "execute_leg": None, "execute_now": False},


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
        'entry_type':"sell",
        'entry_time': entry_time,
        'entry_price': entry_price,
        'sl_hit_price': sl_hit_price,
        'target_price': target_price
    }





def exit_check(df, entry_order_details,squareoff_time):
    entry_symbol = entry_order_details['symbol_to_search']
    entry_time = entry_order_details['entry_time']
    entry_target = entry_order_details['target_price']
    entry_stoploss = entry_order_details['sl_hit_price']
 

    filtered_df = df[(df['Time'] > entry_time) & (df['Time'] <= squareoff_time) & (df['Ticker'] == entry_symbol)]
    sl_filter = filtered_df[(filtered_df['High'] >= entry_stoploss)]
    target_filter = filtered_df[(filtered_df['Low'] <= entry_target)]

    # Find the first row where 'High' is greater than or equal to the exit price
    exit_row = sl_filter

    if not exit_row.empty:
        return exit_row.iloc[0]  # Return the first row meeting the condition
    else:
        return None  # Return None if no row meets the condition









def execute_other_leg(csv_file_path,underlying_symbol, entry_time, squareoff_time, legs):
    df = pd.read_csv(csv_file_path)
    trades_df = pd.DataFrame(columns=['Ticker_Symbol', 'EntryTime', 'EntryPrice', 'EntryType', 'ExitTime', 'ExitPrice', 'ExitType'])
    pending_legs = []
    squareoff_all = []  # List to store legs for later squareoff
    leg_status = {leg['id']: False for leg in legs}  # Initialize status of each leg as False

    # Place legs in pending_legs if execute_now is True
    for leg in legs:
        if leg['execute_now']:
            leg_id = leg['id']
            entry_order_details = place_order_at_atm_price(df,underlying_symbol, leg, entry_time)
            leg_status[leg_id] = True
            pending_legs.append({'id': leg_id, 'leg': leg, 'entry_order_details': entry_order_details})

    # Process pending legs and subsequent legs for each execute_leg_id
    while pending_legs:
        current_pending_legs = pending_legs
        pending_legs = []  # Reset pending_legs for the next iteration
        
        for pending_leg in current_pending_legs:
            leg = pending_leg['leg']
            leg_id = pending_leg['id']
            entry_order_details = pending_leg['entry_order_details']
            exit_row = exit_check(df, entry_order_details, squareoff_time)
            
            if exit_row is not None and not exit_row.empty: 
                exit_price = exit_row['High']
                exit_time = exit_row['Time']
                exit_type = "buy"
                
              
                new_row = pd.DataFrame({
                    'Ticker_Symbol': [entry_order_details['symbol_to_search']],
                    'EntryTime': [entry_order_details['entry_time']],
                    'EntryPrice': [entry_order_details['entry_price']],  # Use entry price of triggering leg for square off
                    'EntryType': [leg['EntryType']],
                    'ExitPrice': [exit_price],
                    'ExitTime': [exit_time],
                    'ExitType': [exit_type]
                })
                trades_df = pd.concat([trades_df, new_row], ignore_index=True)
                
                if leg.get('execute_leg') is not None:
                    for execute_leg_id in leg.get('execute_leg', []):
                        
                        
                            if not leg_status[execute_leg_id]:
                                execute_leg = next((l for l in legs if l['id'] == execute_leg_id), None)
                                if execute_leg:
                                    execute_entry_time = exit_time  # Entry time for the next leg is the exit time of the current leg
                                    entry_order_details = place_order_at_atm_price(df,underlying_symbol, execute_leg, execute_entry_time)
                                    leg_status[execute_leg_id] = True
                                    pending_legs.append({'id': execute_leg_id, 'leg': execute_leg, 'entry_order_details': entry_order_details})
                    
            else:
                leg_to_squareoff = {'id': leg_id, 'entry_order_details': entry_order_details}
                squareoff_all.append(leg_to_squareoff)
    
    # Square off all legs in squareoff_all list at squareoff_time
    for pendingleg in squareoff_all:
        leg_id = pendingleg['id']
        entry_order_details = pendingleg['entry_order_details']
        entry_symbol = entry_order_details['symbol_to_search']
        entry_time = entry_order_details['entry_time']
        entry_price = entry_order_details['entry_price']
        entry_type = entry_order_details['entry_type']
        
        ticker_row_exit = ticker_row_at_time(df, entry_symbol, squareoff_time)

        exit_price= get_ohlc_ticker_row_at_time_t(df, ticker_row_exit, "High")
        exit_time = squareoff_time
        exit_type = "buy"

        new_row = pd.DataFrame({
            'Ticker_Symbol': [entry_symbol],
            'EntryTime': [entry_time],
            'EntryPrice': [entry_price],  # Use entry price of triggering leg for square off
            'EntryType': [entry_type],
            'ExitPrice': [exit_price],
            'ExitTime': [exit_time],
            'ExitType': [exit_type]
        })
        trades_df = pd.concat([trades_df, new_row], ignore_index=True)
    
    trades_df.to_csv(backtest_config['trades_df_csv_path'], index=False)

    return trades_df










entrylegs_details = update_entrylegs_details(backtest_config['entry_csv_file_path'], backtest_config['entrylegs_details'])


#Execute the multi-leg straddle backtest
result = execute_other_leg(backtest_config['entry_csv_file_path'],backtest_config['Underlying_Symbol'],backtest_config['entry_time'],backtest_config['squareoff_time'], backtest_config['entrylegs_details'])
print(result)












