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




def take_reentry(df, trades_df, pending_legs, leg, reentry_entry_time):
    while leg['count'] > 0:
        entry_order_details = place_order_at_atm_price(df, leg, reentry_entry_time)
        exit_row =  exit_check(df,entry_order_details)

        if exit_row is not None:
            exit_price = exit_row['Close']
            exit_time = exit_row['Time']
            exit_type = "Buy"

            trade_details = {
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['entry_time'],
                'EntryPrice': entry_order_details['entry_price'],
                'EntryType': leg['EntryType'],
                'ExitTime': exit_time,
                'ExitPrice': exit_price,
                'ExitType': exit_type
            }
            trades_df = append_trade_to_df(trades_df,  trade_details)
            leg['count'] -= 1
        else:
            if leg not in [p['leg'] for p in pending_legs]:
                pending_legs.append({'leg': leg, 'symbol_to_search': entry_order_details['symbol_to_search']})
            break
    return trades_df, pending_legs

def handle_pending_legs(df, trades_df, pending_legs, squareoff_time):
    for pendingleg in pending_legs:
        leg = pendingleg['leg']
        symbol_to_search = pendingleg['symbol_to_search']
        ticker_row_exit = ticker_row_at_time(df, symbol_to_search, squareoff_time)
        exit_price = ohlc_row_at_time_t(df, ticker_row_exit)
        exit_time = squareoff_time 
        exit_type = 'Buy'

        trade_details = {
            'Symbol': symbol_to_search,
            'EntryTime': leg['entry_time'],  # This assumes entry_time is properly stored in leg
            'EntryPrice': leg['entry_price'],  # Likewise for entry_price
            'EntryType': leg['EntryType'],
            'ExitTime': exit_time,
            'ExitPrice': exit_price,
            'ExitType': exit_type
        }
        trades_df = append_trade_to_df(trades_df, trade_details)

    return trades_df



       
        


def append_trade_to_df(trades_df,trade_details ):
  
    new_row = pd.DataFrame([trade_details])
    return pd.concat([trades_df, new_row], ignore_index=True)
    

def place_order_at_atm_price(df, leg, entry_time):

    atm_row = atm_row_at_time_t(df, entry_time)
    symbol_to_search = f"{leg['Symbol']}{strike_price_row_at_time_t(df, atm_row, entry_time) + leg['offset']}{leg['type']}.NFO"
    ticker_row_entry = ticker_row_at_time(df, symbol_to_search, entry_time)
    entry_price = ohlc_row_at_time_t(df,ticker_row_entry)
    target_price = entry_price * 1.5 if entry_price else None
    
    return {
        'symbol_to_search': symbol_to_search,
        'entry_type':"sell",
        'entry_time': entry_time,
        'entry_price': entry_price,
        'target_price': target_price
    }


def exit_check(df, entry_order_details):
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



          
          

    

   
 
        


            


def straddle_backtest(csv_file_path, entry_time,squareoff_time, legs):
    df = pd.read_csv(csv_file_path)

    trades_df =pd.DataFrame(columns=['Symbol', 'EntryTime', 'EntryPrice','EntryType','ExitTime','ExitPrice', 'ExitType'])
    pending_legs = []
    exit_time = None

   
    for leg in legs:
        entry_order_details = place_order_at_atm_price(df, leg, entry_time)
        symbol_to_search = entry_order_details['symbol_to_search']
        exit_row = exit_check(df,entry_order_details)


        if exit_row is not None and not exit_row.empty: 
            exit_price = exit_row['Close']
            exit_time = exit_row['Time']
            exit_type = "buy"
            reentry_entry_time = exit_time
            trade_details = {
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['entry_time'],
                'EntryPrice': entry_order_details['entry_price'],
                'EntryType': leg['EntryType'],
                'ExitTime': exit_time,
                'ExitPrice': exit_price,
                'ExitType': exit_type
            }
            trades_df = append_trade_to_df(trades_df,  trade_details)
          
            trades_df, pending_legs = take_reentry(df, trades_df, pending_legs, leg,reentry_entry_time)
        
        else:
            ticker_row_exit = ticker_row_at_time(df, symbol_to_search, squareoff_time)
            exit_price = ohlc_row_at_time_t(df, ticker_row_exit)
            exit_time = squareoff_time 



            trade_details = {
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['entry_time'],
                'EntryPrice': entry_order_details['entry_price'],
                'EntryType': leg['EntryType'],
                'ExitTime': exit_time,
                'ExitPrice': exit_price,
                'ExitType': exit_type
            }
            trades_df = append_trade_to_df(trades_df,  trade_details)
       
    handle_pending_legs(df,trades_df,pending_legs,squareoff_time)
    trades_df.to_csv('/Users/pranaygaurav/Downloads/AlgoTrading/KREDENT_TRADING/backinzo/trade_results.csv', index=False)
    return trades_df





csv_file_path = '/Users/pranaygaurav/Downloads/AlgoTrading/KREDENT_TRADING/backinzo/atm_option.csv'
entry_time = "09:19:59"
squareoff_time = "15:24:59"


legs = [
    {'Symbol':'BANKNIFTY06MAR24','type': 'CE','EntryType':"Sell",'ExitType':"Buy" ,'lot_size': 15,'count':1,'offset':600 },   
    {'Symbol':'BANKNIFTY06MAR24','type': 'PE','EntryType':"Sell",'ExitType':"Buy", 'lot_size': 15,'count':1,'offset':-500 },  
  
]

# Execute the multi-leg straddle backtest
result = straddle_backtest(csv_file_path,entry_time,squareoff_time, legs)
print(result)


