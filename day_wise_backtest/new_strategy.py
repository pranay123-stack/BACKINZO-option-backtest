import pandas as pd

# Load the data
file_path = '/Users/pranaygaurav/Downloads/AlgoTrading/Harshul Daga_FNO+IDX/NIFTY+BANKNIFTY_SPOT IDX_Minute Data/2024/JAN_2024/BANKNIFTY_GFDLCM_INDICES_05012024.csv'
df = pd.read_csv(file_path)

# Convert 'Date' and 'Time' columns to a single 'datetime' column
df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M:%S')

# Set the 'datetime' column as the index
df.set_index('datetime', inplace=True)

# Resample the data to 3-minute intervals
resampled_df = df.resample('3T').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum',
   
    
}).dropna()

# Reset the index to get 'datetime' back as columns
resampled_df.reset_index(inplace=True)

# Split 'datetime' back into 'Date' and 'Time'
resampled_df['Date'] = resampled_df['datetime'].dt.strftime('%d/%m/%Y')
resampled_df['Time'] = resampled_df['datetime'].dt.strftime('%H:%M:%S')

# Drop the 'datetime' column
resampled_df.drop(columns=['datetime'], inplace=True)

# Save the resampled data to a new CSV file
output_file_path = '/Users/pranaygaurav/Downloads/AlgoTrading/Backtest_Option_Trading/day_wise_backtest/BANKNIFTY__3min.csv'
resampled_df.to_csv(output_file_path, index=False)

# Display the resampled DataFrame
print(resampled_df)
