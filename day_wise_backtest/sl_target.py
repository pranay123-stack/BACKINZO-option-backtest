import pandas as pd

import re

from Logger import setup_logger
# Setup the logger for this module
logger = setup_logger(__file__)

# Global configuration
backtest_config = {
    "csv_file_path": "/Users/pranaygaurav/Downloads/AlgoTrading/Harshul Daga_FNO+IDX/BACKTEST_ATM/ATM_BANKNIFTY/DEC/ATM_BANKNIFTY_04DEC23.csv",
    "entry_time": "09:19:59",
    "squareoff_time": "15:24:59",
    "stoploss_percentage": 50,
    "target_percentage": 50,
    "sl_hit_condition_check": "premium",
    "after_sl_hit_action": "close the leg",
    "after_target_hit_action": "close the leg",
    "at_squareoff_status": "close the leg",
    "legs": [
        {'id': 1, 'Symbol': 'BANKNIFTY06DEC23', 'type': 'CE', 'EntryType': "Sell", 'ExitType': "Buy", 'lot_size': 15, 'offset': 0, 'execute': True},
        {'id': 2, 'Symbol': 'BANKNIFTY06DEC23', 'type': 'PE', 'EntryType': "Sell", 'ExitType': 'Buy', 'lot_size': 15, 'offset': 0, 'execute': True}
    ]
}



def ATM_round_off(leg,ticker, value):
    try:
        # Ensure ticker is a string
        ticker = str(ticker)
        # Regex to match 'BANKNIFTY' anywhere in the string
        if re.search(r'BANKNIFTY', ticker):
            val =round(value / 100) * 100
            logger.info(f"Rounding value to the nearest hundred for for leg -->leg id {leg['id']} - leg symbol{leg['Symbol']} which is {val}")
          
            return round(value / 100) * 100
        # Regex to match 'NIFTY' anywhere in the string but not when 'BANKNIFTY' is present
        elif re.search(r'NIFTY', ticker) and not re.search(r'BANKNIFTY', ticker):
            val =round(value / 50) * 50
            logger.info(f"Rounding value to the nearest hundred for for leg -->leg id {leg['id']} - leg symbol{leg['Symbol']} which is {val}")
        else:
            logger.error("Ticker does not match either BANKNIFTY or NIFTY")
            return None
    except Exception as e:
        logger.error(f"Error in ATM_round_off: {str(e)}")
        return None


def ticker_row_at_time(df, leg,symbol_to_search, time):
    try:
        val =df[(df['Ticker'] == symbol_to_search) & (df['Time'] == time)]
        logger.info(f"Fetching ticker row for  ticker {symbol_to_search} at square off time {time} of leg{leg} which is {val} ")
       
        return val
    except Exception as e:
        logger.error(f"Error in ticker_row_at_time: {str(e)}")
        return pd.DataFrame()

def atm_row_at_time_t(df, start_time):
    try:
       
        atm_row = df[df['Time'] == start_time]
        logger.info(f"Fetching ATM row at time {start_time}{atm_row}")
        return atm_row
    except Exception as e:
        logger.error(f"Error in atm_row_at_time_t: {str(e)}")
        return pd.DataFrame()

def strike_price_row_at_time_t(df,leg, atm_row, start_time):
    try:
        val =ATM_round_off(leg,str(df.iloc[0]['Ticker']),atm_row.iloc[0]['ATM_close'])
        logger.info(f"Calculating strike price at time {start_time} for leg -->leg id {leg['id']} - leg symbol{leg['Symbol']} which is {val}")
        return val
    except Exception as e:
        logger.error(f"Error in strike_price_row_at_time_t: {str(e)}")
        return None

def ohlc_row_at_time_t(df, ticker_row_at_time):
    try:
        if ticker_row_at_time.empty:
            logger.warning("No data found for ohlc_row_at_time_t")
            return None
        val = ticker_row_at_time.iloc[0]['Close']
        logger.info(f"Fetching OHLC row  {val}")
        return val
    except Exception as e:
        logger.error(f"Error in ohlc_row_at_time_t: {str(e)}")
        return None

def stoploss_price(entry_price, stoploss_percentage):
    try:
        logger.info(f"Calculating stop loss price for entry price {entry_price} and stop loss percentage {stoploss_percentage}")
        sl_multiplier = 1 + (stoploss_percentage / 100)
        sl_hit_price = entry_price * sl_multiplier 
        return sl_hit_price
    except Exception as e:
        logger.error(f"Error in stoploss_price: {str(e)}")
        return None

def target_price_val(entry_price, target_percentage):
    try:
        logger.info(f"Calculating target price for entry price {entry_price} and target percentage {target_percentage}")
        tl_multiplier = target_percentage / 100
        value = entry_price * tl_multiplier
        target_price = entry_price - value
        return target_price
    except Exception as e:
        logger.error(f"Error in target_price_val: {str(e)}")
        return None

def place_order_at_strike_price_at_t(df, leg, entry_time, strike_price, stoploss_percentage, target_percentage):
    try:
        logger.info(f"Placing order at strike price for leg {leg['id']} {leg['Symbol']} at time {entry_time}")
        symbol_to_search = f"{leg['Symbol']}{strike_price}{leg['type']}.NFO"
        ticker_row_entry = ticker_row_at_time(df,leg, symbol_to_search, entry_time)
        entry_price = ohlc_row_at_time_t(df, ticker_row_entry)
        sl_hit_price = stoploss_price(entry_price, stoploss_percentage)
        target_price_value = target_price_val(entry_price, target_percentage)
        leg_entry ={
            'symbol_to_search': symbol_to_search,
            'entry_type': leg["EntryType"],
            'entry_time': entry_time,
            'entry_price': entry_price,
            'Stoploss_price': sl_hit_price,
            'Target_price': target_price_value,
            'exit_type': leg["ExitType"]
        }
        logger.info(f"Placing order at strike price for leg {leg['id']} {leg['Symbol']} at time {entry_time} with close entry price {entry_price} leg entry details {leg_entry}")
        return leg_entry
    except Exception as e:
        logger.error(f"Error in place_order_at_strike_price_at_t: {str(e)}")
        return {}

def find_exit_row_based_on_premium(df, entry_symbol, entry_stoploss, entry_target, entry_time, squareoff_time):
    try:
        logger.info(f"Finding exit row based on premium for symbol {entry_symbol} between {entry_time} and {squareoff_time}")
        filtered_df = df[(df['Time'] > entry_time) & (df['Time'] <= squareoff_time) & (df['Ticker'] == entry_symbol)]
        c1 = filtered_df[(filtered_df['High'] >= entry_stoploss)]
        c2 = filtered_df[(filtered_df['Low'] <= entry_target)]
        status = None
        exit_row = pd.DataFrame()
        if not c1.empty:
            exit_row = filtered_df[(filtered_df['High'] >= entry_stoploss)]
            status = "slhit"
        elif not c2.empty:
            exit_row = filtered_df[(filtered_df['Low'] <= entry_target)]
            status = "targethit"
        else:
            status = "squareoff"
        return exit_row, status
    except Exception as e:
        logger.error(f"Error in find_exit_row_based_on_premium: {str(e)}")
        return pd.DataFrame(), "error"

def handle_stop_loss_hit(entry, sl_hit_exit_row, action, trades_df):
    try:
        logger.info(f"Handling stop loss hit at high value {sl_hit_exit_row.iloc[0]['High']} for leg {entry['LegID']}{entry['Symbol']}")
        pnl = (entry['EntryPrice'] - sl_hit_exit_row.iloc[0]['High']) * 15
        new_row = pd.DataFrame({
            'LegID': [entry['LegID']],
            'Symbol': [entry['Symbol']],
            'EntryTime': [entry['EntryTime']],
            'EntryPrice': [entry['EntryPrice']],
            'EntryType': [entry['EntryType']],
            'ExitType': [entry['ExitType']],
            'ExitTime': [sl_hit_exit_row.iloc[0]['Time']],
            'ExitPrice': [sl_hit_exit_row.iloc[0]['High']],
            'status': [action],
            'slhit': "yes",
            'targethit': "No",
            "pnl": pnl
        })
        trades_df = pd.concat([trades_df, new_row], ignore_index=True)
        return trades_df
    except Exception as e:
        logger.error(f"Error in handle_stop_loss_hit: {str(e)}")
        return trades_df

def handle_target_hit(entry, target_hit_exit_row, action, trades_df):
    try:
        val =  target_hit_exit_row.iloc[0]['Low']
        logger.info(f"Handling target hit at low value {val} for leg {entry['LegID']}{entry['Symbol']}")
        pnl = (entry['EntryPrice'] - val) * 15
        new_row = pd.DataFrame({
            'LegID': [entry['LegID']],
            'Symbol': [entry['Symbol']],
            'EntryTime': [entry['EntryTime']],
            'EntryPrice': [entry['EntryPrice']],
            'EntryType': [entry['EntryType']],
            'ExitType': [entry['ExitType']],
            'ExitTime': [target_hit_exit_row.iloc[0]['Time']],
            'ExitPrice': [target_hit_exit_row.iloc[0]['Low']],
            'status': [action],
            'slhit': "No",
            'targethit': "Yes",
            "pnl": pnl
        })
        trades_df = pd.concat([trades_df, new_row], ignore_index=True)
        return trades_df
    except Exception as e:
        logger.error(f"Error in handle_target_hit: {str(e)}")
        return trades_df



def process_single_leg(df, leg, entry_time, stoploss_percentage, target_percentage):
    try:
        logger.info(f"Processing single leg {leg['id']}{leg['Symbol']}")
        if leg['execute']:
            strike_price = strike_price_row_at_time_t(df, leg,atm_row_at_time_t(df, entry_time), entry_time) + leg['offset']
            entry_order_details = place_order_at_strike_price_at_t(df, leg, entry_time, strike_price, stoploss_percentage, target_percentage)
            return {
                'LegID': leg['id'],
                'Symbol': entry_order_details['symbol_to_search'],
                'EntryTime': entry_order_details['entry_time'],
                'EntryPrice': entry_order_details['entry_price'],
                'EntryType': entry_order_details['entry_type'],
                'Stoploss': entry_order_details['Stoploss_price'],
                'Target': entry_order_details['Target_price'],
                'ExitType': entry_order_details['exit_type'],
                'LegInfo': leg
            }
        else:
            logger.info(f"Leg {leg['id']} execution skipped")
            return None
    except Exception as e:
        logger.error(f"Error in process_single_leg: {str(e)}")
        return None

def process_entries(df, legs, entry_time, stoploss_percentage, target_percentage):
    try:
        logger.info(f"Processing entries for two legs  for combination sl {stoploss_percentage} and target{target_percentage}")
        entries = []
        for leg in legs:
            logger.info(f"Processing entry of leg { leg['id']} { leg['Symbol']}")
            entry = process_single_leg(df, leg, entry_time, stoploss_percentage, target_percentage)
            if entry:
                entries.append(entry)
        return entries
    except Exception as e:
        logger.error(f"Error in process_entries: {str(e)}")
        return []

def process_exits(df, entries, trades_df, squareoff_time):
    try:
        logger.info("Processing exits for all entries")
        pending_leg_positions = []
        for entry in entries:
            logger.info(f"Processing exit of ---{entry['LegID']} ----{entry['Symbol']}")
            if backtest_config["sl_hit_condition_check"] == "premium":
                exit_row, status = find_exit_row_based_on_premium(df, entry['Symbol'], entry['Stoploss'], entry['Target'], entry["EntryTime"], squareoff_time)
            elif backtest_config["sl_hit_condition_check"] == "underlying_points":
                raise ValueError("Unsupported stop-loss condition type")
            else:
                raise ValueError("Unsupported stop-loss condition type")
            if not exit_row.empty:
                if status == "slhit" and backtest_config['after_sl_hit_action'] == "close the leg":
                    trades_df = handle_stop_loss_hit(entry, exit_row, backtest_config['after_sl_hit_action'], trades_df)
                elif status == "targethit" and backtest_config['after_target_hit_action'] == "close the leg":
                    trades_df = handle_target_hit(entry, exit_row, backtest_config['after_target_hit_action'], trades_df)
            elif exit_row.empty and status == "squareoff" and backtest_config['at_squareoff_status'] == "close the leg":
                pending_leg_positions.append(entry)
        return trades_df, pending_leg_positions
    except Exception as e:
        logger.error(f"Error in process_exits: {str(e)}")
        return trades_df, []

def process_pending_legs(df, pending_leg_positions, squareoff_time, trades_df):
    try:
        logger.info("=====================process_pending_legs()===============")
        if not pending_leg_positions :
             logger.info("no pendind legs left to squareoff at square off time.=====================so now testing next combination")
        for pending_leg in pending_leg_positions:
         
            exit_price_at_squareoff = ohlc_row_at_time_t(df, ticker_row_at_time(df, pending_leg,pending_leg['Symbol'], squareoff_time))
            logger.info(f"Processing pending leg at close price at squareoff {exit_price_at_squareoff}{pending_leg['LegID']} {pending_leg['Symbol']}")
            pnl = (pending_leg['EntryPrice'] - exit_price_at_squareoff) * 15
            new_row = pd.DataFrame({
                'LegID': [pending_leg['LegID']],
                'Symbol': [pending_leg['Symbol']],
                'EntryTime': [pending_leg['EntryTime']],
                'EntryPrice': [pending_leg['EntryPrice']],
                'EntryType': [pending_leg['EntryType']],
                'ExitType': [pending_leg['ExitType']],
                'ExitTime': [squareoff_time],
                'ExitPrice': [exit_price_at_squareoff],
                'status': [backtest_config["at_squareoff_status"]],
                'slhit': "No",
                'targethit': "No",
                "pnl": pnl
            })
            trades_df = pd.concat([trades_df, new_row], ignore_index=True)
        return trades_df
    except Exception as e:
        logger.error(f"Error in process_pending_legs: {str(e)}")
        return trades_df

def squareoff_premium(backtest_config, stoploss_percentage, target_percentage):
    try:
        logger.info(f"===========================squareoff_premium() of sl percentage: {stoploss_percentage} and target percentage: {target_percentage}================")
        df = pd.read_csv(backtest_config['csv_file_path'])
        trades_df = pd.DataFrame(columns=['LegID', 'Symbol', 'EntryTime', 'EntryPrice', 'EntryType', 'ExitType', 'ExitTime', 'ExitPrice', 'status', 'slhit', 'targethit', 'pnl', 'StopLossPercentage', 'TargetPercentage', 'total'])
        pending_leg_positions = []
        entries = process_entries(df, backtest_config['legs'], backtest_config['entry_time'], stoploss_percentage, target_percentage)
        trades_df, pending_leg_positions = process_exits(df, entries, trades_df, backtest_config['squareoff_time'])
        trades_df = process_pending_legs(df, pending_leg_positions, backtest_config['squareoff_time'], trades_df)
        trades_df['StopLossPercentage'] = stoploss_percentage
        trades_df['TargetPercentage'] = target_percentage
        total_pnl = trades_df['pnl'].sum()
        trades_df['total'] = total_pnl
        return trades_df
    except Exception as e:
        logger.error(f"Error in squareoff_premium: {str(e)}")
        return pd.DataFrame()

def run_all_combinations(backtest_config):
    try:
        logger.info(f"===========Running all combinations of stop loss and target percentages{backtest_config['csv_file_path']}=========")
        all_combinations_df = pd.DataFrame()
        for sl in range(5, 101, 5):
            for tp in range(5, 101, 5):
                logger.info(f"====================Running stop loss percentage: {sl} and target percentage: {tp}===============")
                logger.info(f"===========================================================================================================================")
                logger.info(f"===========================================================================================================================")
                logger.info(f"===========================================================================================================================")
                logger.info(f"===========================================================================================================================")
                result_df = squareoff_premium(backtest_config, sl, tp)
                all_combinations_df = pd.concat([all_combinations_df, result_df], ignore_index=True)
                all_combinations_df.loc[all_combinations_df.index[-1], 'Total PnL'] = result_df['total'].iloc[0]
        all_combinations_df.to_csv('/Users/pranaygaurav/Downloads/AlgoTrading/Harshul Daga_FNO+IDX/BACKTEST_ATM/ATM_BANKNIFTY/DEC/trade/trade.csv', index=False)
        return all_combinations_df
    except Exception as e:
        logger.error(f"Error in run_all_combinations: {str(e)}")
        return pd.DataFrame()

def create_pivot_table(all_combinations_df):
    try:
        logger.info(f"==========create_pivot_table()=============")
        pivot_table = all_combinations_df.pivot_table(values='Total PnL', index='TargetPercentage', columns='StopLossPercentage', aggfunc='first')
        pivot_table.to_excel('/Users/pranaygaurav/Downloads/AlgoTrading/Harshul Daga_FNO+IDX/BACKTEST_ATM/ATM_BANKNIFTY/DEC/excel/total_pnl_excel.xlsx')
        return pivot_table
    except Exception as e:
        logger.error(f"Error in create_pivot_table: {str(e)}")
        return pd.DataFrame()

# Run the backtest for all combinations
try:
    final_results = run_all_combinations(backtest_config)
    print(final_results)
    pivot_table = create_pivot_table(final_results)
    print(pivot_table)
except Exception as e:
    logger.error(f"Error in main execution block: {str(e)}")


#entry-close
#exit-high
#target-low