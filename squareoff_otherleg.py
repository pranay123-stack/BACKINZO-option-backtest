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
        {'id': 1, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 500, 'squareoff_id': [2, 3,]},
        {'id': 2, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 0, 'squareoff_id': [3, 4,5]},
        {'id': 3, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': 0, 'squareoff_id': [4,5,6]},
        {'id': 4, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': -600, 'squareoff_id': []},
        {'id': 5, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': -700, 'squareoff_id': [1]},
        {'id': 6, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 0, 'offset': -800, 'squareoff_id': [1]}

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



def other_leg_to_squareoff(df, trades_df, slhitleg, leg_status, pending_legs,exit_time):
    squareoff_id_list =None
    for pending_leg_entry in pending_legs:
        if pending_leg_entry['leg'] == slhitleg:  # Find the slhitleg in pending_legs
            squareoff_id_list = pending_leg_entry['leg']['squareoff_id']
            print(squareoff_id_list)
            break

    for squareoff_id in squareoff_id_list:
        if not leg_status[squareoff_id]:  # If the leg hasn't been squared off yet
            for pending_leg_entry in pending_legs:
                if pending_leg_entry['id'] == squareoff_id:
                    squareoff_entry_order_details = pending_leg_entry['entry_order_details']
                    squareoff_symbol_to_search = squareoff_entry_order_details['symbol_to_search']
                    squareoff_entry_time = squareoff_entry_order_details['entry_time']
                    squareoff_entry_price = squareoff_entry_order_details['entry_price']
                    squareoff_entry_type = squareoff_entry_order_details['entry_type']
                    
                    
                    ticker_row_exit = ticker_row_at_time(df,  squareoff_symbol_to_search, exit_time)
                    exit_price = ohlc_row_at_time_t2(df, ticker_row_exit)
                    

        
                                
                    new_row = pd.DataFrame({
                            'Symbol': [squareoff_symbol_to_search],
                            'EntryTime': [squareoff_entry_time],
                            'EntryPrice': [squareoff_entry_price],  # Use entry price of triggering leg for square off
                            'EntryType': [squareoff_entry_type],
                            'ExitPrice': [exit_price],
                            'ExitTime': [exit_time],
                            'ExitType': "buy"
                    })
                    trades_df = pd.concat([trades_df, new_row], ignore_index=True)
                    leg_status[squareoff_id] = True  # Mark the squareoff leg as squared off
                    break  # No need to continue searching once a match is found

    return trades_df, pending_legs

def handle_pending_legs(df, trades_df, pending_legs,leg_status, squareoff_time):
    for pendingleg in pending_legs:
        leg_id = pendingleg['id']
        if  leg_status[leg_id] == False :
            entry_order_details = pendingleg['entry_order_details']
            entry_symbol = entry_order_details['symbol_to_search']
            entry_time = entry_order_details['entry_time']
            entry_price = entry_order_details['entry_price']
            entry_type = entry_order_details['entry_type']
            ticker_row_exit = ticker_row_at_time(df,  entry_symbol, squareoff_time)
            exit_price = ohlc_row_at_time_t2(df, ticker_row_exit)
            exit_time = squareoff_time 
            exit_type = "buy"

            new_row = pd.DataFrame({
                    'Symbol': [entry_symbol],
                    'EntryTime': [entry_time],
                    'EntryPrice': [entry_price],  # Use entry price of triggering leg for square off
                    'EntryType': [entry_type],
                    'ExitPrice': [exit_price],
                    'ExitTime': [exit_time],
                    'ExitType': [exit_type]
                })
            trades_df = pd.concat([trades_df, new_row], ignore_index=True)
            leg_status[ leg_id] = True  # Mark the squareoff leg as squared off





    

    

    return trades_df





def exit_check(df, entry_order_details,squareoff_time):
    symbol_to_search = entry_order_details['symbol_to_search']
    entry_time = entry_order_details['entry_time']
    target_price = entry_order_details['target_price']
 
    # Filter DataFrame for the specified symbol and within the time range
    filtered_df = df[(df['Ticker'] == symbol_to_search) & 
                     (df['Time'] > entry_time) & 
                     (df['Time'] < squareoff_time)]

    # Find the first row where 'High' is greater than or equal to the exit price
    exit_row = filtered_df[filtered_df['High'] >= target_price]

    if not exit_row.empty:
        return exit_row.iloc[0]  # Return the first row meeting the condition
    else:
        return None  # Return None if no row meets the condition


def place_all_legs_entry_orders(df, legs, entry_time):
    pending_legs = []
    for leg in legs:
        leg_id = leg['id']
        entry_order_details = place_order_at_atm_price(df, leg, entry_time)
        pending_legs.append({'id': leg_id, 'leg': leg, 'entry_order_details': entry_order_details})
    return pending_legs


def squareoff_other_leg(csv_file_path, entry_time, squareoff_time, legs):
    df = pd.read_csv(csv_file_path)
    trades_df = pd.DataFrame(columns=['Symbol', 'EntryTime', 'EntryPrice','EntryType','ExitTime','ExitPrice', 'ExitType'])
    pending_legs = []
    exit_time = None
    leg_status = {leg['id']: False for leg in legs}  # Initialize status of each leg as False
    pending_legs = place_all_legs_entry_orders(df, legs, entry_time)

    # Process pending legs
    for pending_leg in pending_legs:
        leg = pending_leg['leg']
        leg_id = leg['id']
        if not leg_status[leg_id]:  # Check if leg status is False
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
                leg_status[leg_id] = True 

                trades_df, pending_legs = other_leg_to_squareoff(df, trades_df, leg, leg_status, pending_legs,exit_time)
            
    # Handle any remaining pending legs
    trades_df = handle_pending_legs(df, trades_df, pending_legs,leg_status, squareoff_time)
    
    trades_df.to_csv('/Users/pranaygaurav/Downloads/AlgoTrading/KREDENT_TRADING/backinzo/trade_results.csv', index=False)
    return trades_df



# Execute the multi-leg straddle backtest
result = squareoff_other_leg(csv_file_path,entry_time,squareoff_time, entrylegs_details)
print(result)









