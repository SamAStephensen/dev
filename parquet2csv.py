import pandas as pd
import os

def convert_parquet_to_csv(parquet_file, csv_folder):
    """
    Converts a single Parquet file to CSV and saves it in a specified folder.

    Args:
        parquet_file (str): Path to the Parquet file to be converted.
        csv_folder (str): Path to the folder where the CSV file will be saved.
    """
    # Ensure the CSV folder exists
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)

    try:
        # Read the Parquet file into a DataFrame
        df = pd.read_parquet(parquet_file, engine='pyarrow')

        # Get the file name without extension and create the corresponding CSV path
        file_name = os.path.basename(parquet_file).replace('.parquet', '.csv')
        csv_path = os.path.join(csv_folder, file_name)
      
        df.to_csv(csv_path, index=False)

        print(f"Converted {parquet_file} to {csv_path}")

    except Exception as e:
        print(f"Failed to convert {parquet_file}: {e}")

# Example usage
if __name__ == "__main__":
    parquet_file = "./parquet_files/data1.parquet"  # Replace with the Parquet file you want to convert
    csv_folder = "./csv_files"  # Replace with your desired CSV folder path
    convert_parquet_to_csv(parquet_file, csv_folder)
