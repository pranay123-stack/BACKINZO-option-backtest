import pandas as pd
import numpy as np
import logging
from datetime import datetime

import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, filename='trading_log.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')




# Global configuration
backtest_config = {
    "index_csv_file_path_0" :"/Users/pranaygaurav/Downloads/AlgoTrading/Backtest_Option_Trading/month_wise_backtest/SUPERTREND/DATA/INDEX_JAN_2024/BANKNIFTY_GFDLCM_INDICES_02012024.csv",
    "index_csv_file_path": "/Users/pranaygaurav/Downloads/AlgoTrading/Backtest_Option_Trading/month_wise_backtest/SUPERTREND/DATA/INDEX_JAN_2024/BANKNIFTY_GFDLCM_INDICES_03012024.csv",
    "ticker_csv_file_path": "/Users/pranaygaurav/Downloads/AlgoTrading/Backtest_Option_Trading/month_wise_backtest/SUPERTREND/DATA/TICKER_JAN_2024/ATM_BANKNIFTY_03JAN24.csv",
    "trades_df_csv_path" : "/Users/pranaygaurav/Downloads/AlgoTrading/trades_df.csv",
    "signals_df_csv_path" : "/Users/pranaygaurav/Downloads/AlgoTrading/signals_df.csv",
    "squareoff_time": "15:30:59",
    "stoploss_percentage": 50,
    "target_percentage": 50,
    "Underlying_Symbol":"",
    "entrylegs_details": [
    {'id': 1, 'Ticker_Symbol': '', 'type': 'CE', 'EntryType': "Buy", 'ExitType': "Sell", 'lot_size': 0, 'offset': 0},
    {'id': 2, 'Ticker_Symbol': '', 'type': 'PE', 'EntryType': "Buy", 'ExitType': "Sell", 'lot_size': 0, 'offset': 0},
    ],
    
    "Technical_Indicator_Details": {
    
      "SUPERTREND": {
        "atr_period": 10,
        "multiplier": 3,
      }
    
    }

   

  
}



def calculate_supertrend(df, period, multiplier):
    logging.info("Starting Supertrend calculation")

        # Ensure DateTime column is in datetime format
    df['DateTime'] = pd.to_datetime(df['DateTime'])

    # Calculate HL2
    df['hl2'] = (df['High'] + df['Low']) / 2

    # logging.info("\nCalculated HL2:\n" + df.to_string())



    # Calculate True Range (TR)
    df['tr'] = np.maximum((df['High'] - df['Low']),
                          np.maximum(abs(df['High'] - df['Close'].shift(1)),
                                     abs(df['Low'] - df['Close'].shift(1))))
    # logging.info("\nCalculated TRue Range:\n" + df.to_string())

    # Calculate ATR
    df['atr'] = df['tr'].rolling(window=period).mean()
    # logging.info("\nCalculated Average TRue Range:\n" + df.to_string())

    # Calculate basic upper and lower bands
    df['basic_upper_band'] = df['hl2'] + (multiplier * df['atr'])
    df['basic_lower_band'] = df['hl2'] - (multiplier * df['atr'])

    # logging.info("\nCalculated basic upper and lower bands:\n" + df.to_string())
       # Filter the DataFrame to show rows starting from the specified time
    filter_time = pd.to_datetime("09:15:59").time()
    filtered_df = df[df['DateTime'].dt.time >= filter_time]

    # Log the filtered DataFrame
    logging.info("\nCalculated basic upper and lower bands:\n" + filtered_df.to_string())
  

    # Initialize upper and lower bands
    df['upper_band'] = np.nan
    df['lower_band'] = np.nan
    logging.info("Initialized upper and lower bands")

    for i in range(period, len(df)):
        df['upper_band'].iat[i] = df['basic_upper_band'].iat[i] if (df['basic_upper_band'].iat[i] < df['upper_band'].iat[i-1]) or (df['Close'].iat[i-1] > df['upper_band'].iat[i-1]) else df['upper_band'].iat[i-1]
        df['lower_band'].iat[i] = df['basic_lower_band'].iat[i] if (df['basic_lower_band'].iat[i] > df['lower_band'].iat[i-1]) or (df['Close'].iat[i-1] < df['lower_band'].iat[i-1]) else df['lower_band'].iat[i-1]
        if i % 100 == 0:  # Log progress every 100 iterations
            logging.info(f"Processed {i} rows for upper and lower bands")

    # Determine trend direction
    df['supertrend'] = np.nan
    df['trend'] = np.nan
    logging.info("Initialized Supertrend and trend columns")

    for i in range(period, len(df)):
        if df['Close'].iat[i] > df['upper_band'].iat[i-1]:
            df['supertrend'].iat[i] = df['lower_band'].iat[i]
            df['trend'].iat[i] = 'up'
        elif df['Close'].iat[i] < df['lower_band'].iat[i-1]:
            df['supertrend'].iat[i] = df['upper_band'].iat[i]
            df['trend'].iat[i] = 'down'
        else:
            df['supertrend'].iat[i] = df['supertrend'].iat[i-1]
            df['trend'].iat[i] = df['trend'].iat[i-1]
        if i % 100 == 0:  # Log progress every 100 iterations
            logging.info(f"Processed {i} rows for trend determination")

    logging.info("Supertrend calculation completed")
    return df










def process_data(file_path,legs):
    df = pd.read_csv(file_path)
    df0 = pd.read_csv(backtest_config['index_csv_file_path_0'])
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])  # Combining Date and Time into a single DateTime column
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time

    df0['DateTime'] = pd.to_datetime(df0['Date'] + ' ' + df0['Time'])
    df0['Time'] = pd.to_datetime(df0['Time'], format='%H:%M:%S').dt.time

    start_time = pd.to_datetime('09:15:59', format='%H:%M:%S').time()
    end_time = pd.to_datetime(backtest_config['squareoff_time'], format='%H:%M:%S').time()
    
    filtered_df = df[(df['Time'] <= end_time) & (df['Time'] >= start_time)].copy()
    final_df = filtered_df.copy()

    period = backtest_config['Technical_Indicator_Details']['SUPERTREND']['atr_period']

    filtered_df0 = df0[(df0['Time'] <= end_time) & (df0['Time'] >= start_time)].copy()

    # Extract rows from df0 starting from 15:30:59 to period - 1
    target_time = pd.to_datetime('15:30:59', format='%H:%M:%S').time()
    idx = filtered_df0[filtered_df0['Time'] == target_time].index[0]
    rows_to_add = filtered_df0.loc[idx - period+1:idx + 1]  # Adjust slicing to include the exact number of rows needed

    # Log the DataFrames
    # logging.info("\nFinal DF:\n" + final_df.to_string())
    # logging.info("\nRows to Add DF0:\n" + rows_to_add.to_string())

    # Concatenate the selected rows from final_df0 to the beginning of final_df
    merged_df = pd.concat([rows_to_add, final_df]).reset_index(drop=True)

    # # Log the merged DataFrame
    # logging.info("\nMerged DF:\n" + merged_df.to_string())




    

    ticker_df = pd.read_csv(backtest_config['ticker_csv_file_path'])  # Read ticker options CSV

   
    # multiplier = backtest_config['Technical_Indicator_Details']['SUPERTREND']['multiplier']
   
    period = 10  # Example period
    multiplier = 3  # Example multiplier

    # ffinal_df = calculate_supertrend( final_df0,final_df, period, multiplier)
    # logging.info(ffinal_df[['DateTime', 'Open', 'High', 'Low', 'Close', 'supertrend', 'trend']])
    
      # Calculate the Supertrend from 09:15:00
    merged_df = calculate_supertrend(merged_df, period, multiplier)

    logging.info(merged_df[['DateTime', 'Open', 'High', 'Low', 'Close', 'supertrend', 'trend']])

   

   

 






# Provide your CSV file path here
file_path = backtest_config.get('index_csv_file_path')
process_data(file_path,backtest_config['entrylegs_details'])


