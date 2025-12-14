# utils.py

import random
import datetime
import numpy as np
import pandas as pd
import os
import math
import logging
import os

def get_random_date(start_date, end_date):
    """
    Generates a random date between two given dates.

    Args:
        start_date (datetime.date): The start of the date range.
        end_date (datetime.date): The end of the date range.

    Returns:
        datetime.date: A random date within the specified range.
    """
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + datetime.timedelta(days=random_number_of_days)
    return random_date

def generate_id(prefix, last_id,num_digits):
    """
    Generates a new sequential ID with a given prefix, incrementing from the last known ID.

    Args:
        prefix (str): The string prefix for the ID (e.g., 'CUST').
        last_id (str or None): The last generated ID to increment from. If None or invalid, starts from 1.
        num_digits (int): The number of digits the numeric part of the ID should have, padded with leading zeros if necessary.

    Returns:
        str: The newly generated sequential ID (e.g., 'CUST00001').
    """
    if last_id is not None:
        try:
            current_number = int(last_id[len(prefix):])
            next_number = current_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    formatted_number = str(next_number).zfill(num_digits)
    return prefix + formatted_number

def get_random_date_in_range(start_date, days_ahead_min, days_ahead_max):
    """
    Generates a random date that is a certain number of days ahead of a given start date.

    Args:
        start_date (datetime.date): The base date from which to calculate the future date.
        days_ahead_min (int): The minimum number of days to add to the start date.
        days_ahead_max (int): The maximum number of days to add to the start date.

    Returns:
        datetime.date: A random date in the future, based on the specified range.
    """
    days_ahead = random.randint(days_ahead_min, days_ahead_max)
    return start_date + datetime.timedelta(days=days_ahead)

def weighted_choice(choices, weights):
    """
    Selects a single item from a list of choices based on a corresponding list of weights.

    Args:
        choices (list): A list of items to choose from.
        weights (list): A list of numeric weights corresponding to the choices. Must be the same length as choices.

    Returns:
        any: A single element selected from the 'choices' list based on the provided weights.
    """
    return random.choices(choices, weights=weights, k=1)[0]

def calculate_net_value(quantity, unit_price):
    """
    Calculates the net value by multiplying quantity and unit price, rounded to 2 decimal places.

    Args:
        quantity (int or float): The number of units.
        unit_price (float): The price per unit.

    Returns:
        float: The calculated net value (quantity * unit_price), rounded to two decimal places.
    """
    return round(quantity * unit_price, 2)

def save_dataframe(df, filename, output_dir, output_format):
    """
    Saves a pandas DataFrame to a file in either CSV or Parquet format.

    This function will create the output directory if it does not already exist.

    Args:
        df (pd.DataFrame): The DataFrame to be saved.
        filename (str): The name of the output file (e.g., 'data.csv').
        output_dir (str): The directory where the file will be saved.
        output_format (str): The format to save the file in. Supported values are "csv" and "parquet".

    Returns:
        None: This function does not return a value. It prints a confirmation message to the console.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    if output_format == "csv":
        df.to_csv(filepath, index=False)
    elif output_format == "parquet":
        df.to_parquet(filepath, index=False)
    logging.info(f"Saved {len(df)} records to {filepath}")


def save_generator_to_dataframe(generator_func, filename, output_dir, output_format, chunk_size=10000):
    """
    Reads rows from a generator function, accumulates them into DataFrames in chunks,
    and then saves these DataFrames to a file in either CSV or Parquet format.
    Args:
        generator_func (callable): A function that, when called, returns a generator
                                   yielding dictionaries or lists representing rows.
                                   
        filename (str): The name of the output file (e.g., 'data.csv').

        output_dir (str): The directory where the file will be saved.

        output_format (str): The format to save the file in. Supported values are "csv" and "parquet".

        chunk_size (int): The number of rows to accumulate before writing a chunk to the file.
                          
    Returns:
        None: This function does not return a value. It prints a confirmation message to the console.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    total_records_saved = 0
    first_chunk = True
    rows_buffer = []

    try:
        for row in generator_func():
            rows_buffer.append(row)

            if len(rows_buffer) >= chunk_size:
                df_chunk = pd.DataFrame(rows_buffer)
                
                if output_format == "csv":
                    # For CSV, append if not the first chunk, otherwise write header
                    df_chunk.to_csv(filepath, mode='a' if not first_chunk else 'w', 
                                    header=first_chunk, index=False)
                elif output_format == "parquet":
                    pass 
                else:
                    logging.error(f"Unsupported output format: {output_format}")
                    return

                total_records_saved += len(df_chunk)
                #logging.info(f"Processed and saved {len(df_chunk)} records. Total: {total_records_saved}")
                rows_buffer = []  # Clear buffer
                first_chunk = False

        # Save any remaining rows in the buffer
        if rows_buffer:
            df_chunk = pd.DataFrame(rows_buffer)
            if output_format == "csv":
                df_chunk.to_csv(filepath, mode='a' if not first_chunk else 'w', 
                                header=first_chunk, index=False)
            elif output_format == "parquet":
                pass # Handled below
            
            total_records_saved += len(df_chunk)
            #logging.info(f"Processed and saved {len(df_chunk)} remaining records. Total: {total_records_saved}")

        # For Parquet, if we accumulated all data in memory (which is the default behavior
        # for `pd.to_parquet` when not using a streaming writer), we need to create
        # the full DataFrame and save it.
        if output_format == "parquet":
            pass
            
            logging.info(f"Saved {total_records_saved} records to {filepath}")

    except Exception as e:
        logging.error(f"An error occurred while saving data: {e}")
        raise # Re-raise the exception after logging
     
    logging.info(f"Saved {total_records_saved} records to {filepath}")
    logging.info(f"{filename} data successfully saved to {filepath} in csv format.")






def log_normal_int(mean, std_dev_factor=0.5, min_val=1, max_val=None):
    """
    Generates an integer from a log-normal distribution, clamped within a min/max range.

    This is useful for creating realistic-looking skewed data, such as order quantities or prices.

    Args:
        mean (float): The desired mean of the distribution.
        std_dev_factor (float, optional): A factor to determine the standard deviation relative to the mean. Defaults to 0.5.
        min_val (int, optional): The minimum value for the returned integer. Defaults to 1.
        max_val (int or None, optional): The maximum value for the returned integer. If None, no upper limit is applied. Defaults to None.

    Returns:
        int: An integer sampled from the log-normal distribution, clamped between min_val and max_val.
    """
    # Adjust mean for log-normal distribution
    mu = np.log(mean**2 / np.sqrt(mean**2 + (mean * std_dev_factor)**2))
    sigma = np.sqrt(np.log(1 + (mean * std_dev_factor)**2 / mean**2))
    val = int(np.round(np.random.lognormal(mu, sigma)))
    if max_val is not None:
        return max(min_val, min(max_val, val))
    return max(min_val, val)

def get_q4_multiplier(q4_increase_percentage,start_date, end_dat):
    """
    Returns a multiplier to simulate increased activity during the fourth quarter (Q4).

    Args:
        date (datetime.date): The date to check if it falls within Q4 (October, November, December).
        q4_increase_percentage (float): The percentage increase as a decimal (e.g., 0.2 for a 20% increase).

    Returns:
        float: A multiplier of (1 + q4_increase_percentage) if the date is in Q4, otherwise returns 1.0.
    """
    date=get_random_date(start_date,end_dat)
    ran_num=random.random()
    while ran_num<q4_increase_percentage:
        if date.month in [10,11,12]:
            return date 
        else:
            date=get_random_date(start_date,end_dat)
    return date

def get_delivery_delay_days(delay_distribution):
    """
    Calculates a random number of delivery delay days based on a weighted distribution of time ranges.

    Args:
        delay_distribution (dict): A dictionary where keys are strings representing delay ranges
                                   (e.g., '1-7_days', '8-14_days') and values are the weights (probabilities)
                                   for those ranges.

    Returns:
        int: A random integer representing the number of delay days. Returns 0 if the chosen range
             is not recognized or if an unexpected choice is made.
    """
    choice = weighted_choice(list(delay_distribution.keys()), list(delay_distribution.values()))
    if choice == '1-7_days':
        return random.randint(1, 7)
    elif choice == '8-14_days':
        return random.randint(8, 14)
    elif choice == '15-30_days':
        return random.randint(15, 30)
    return 0 # Should not happen if distribution sums to 1


def _validate_configuration_variables(self, key_name, type,num_type=None, min_val=None, max_val=None, exclusive_min=False, exclusive_max=False):
        """
        Helper method to validate if a config value is Valid
        """
        if not hasattr(self.config, key_name):
            raise AttributeError(f"Configuration key '{key_name}' is not found in the current config file.")

        actual_value = getattr(self.config, key_name)

        if not isinstance(actual_value, type):
            raise ValueError(f"Configuration key '{key_name}' must be a {type}.")

        if type is tuple:
            
            for i, x in enumerate(actual_value):
                if not isinstance(x, num_type):
                    raise ValueError(f"Configuration key '{key_name}' must be a tuple of {num_type.__name__} values. "
                                        f"Element at index {i} is of type {type(x).__name__}.")

                if num_type in (float, int): # Apply number-specific checks
                    if math.isinf(x) or math.isnan(x):
                        raise ValueError(f"Configuration key '{key_name}' contains an invalid number (infinity or NaN) at index {i}.")

                    if min_val is not None:
                        if exclusive_min and x <= min_val:
                            raise ValueError(f"Configuration key '{key_name}' element at index {i} must be strictly greater than {min_val}.")
                        elif not exclusive_min and x < min_val:
                            raise ValueError(f"Configuration key '{key_name}' element at index {i} must be greater than or equal to {min_val}.")

                    if max_val is not None:
                        if exclusive_max and x >= max_val:
                            raise ValueError(f"Configuration key '{key_name}' element at index {i} must be strictly less than {max_val}.")
                        elif not exclusive_max and x > max_val:
                            raise ValueError(f"Configuration key '{key_name}' element at index {i} must be less than or equal to {max_val}.")

        elif type in(int, float):
            x=actual_value
            if min_val is not None:
                if exclusive_min and x <= min_val:
                    raise ValueError(f"Configuration key '{key_name}' element  must be strictly greater than {min_val}.")
                elif not exclusive_min and x < min_val:
                    raise ValueError(f"Configuration key '{key_name}' element  must be greater than or equal to {min_val}.")
    
            if max_val is not None:
                if exclusive_max and x >= max_val:
                    raise ValueError(f"Configuration key '{key_name}' element  must be strictly less than {max_val}.")
                elif not exclusive_max and x > max_val:
                    raise ValueError(f"Configuration key '{key_name}' element  must be less than or equal to {max_val}.")
        
        elif type is list:

            for i, x in enumerate(actual_value):
                if not isinstance(x, num_type):
                    raise ValueError(f"Configuration key '{key_name}' must be a tuple of {num_type.__name__} values. "
                                        f"Element at index {i} is of type {type(x).__name__}.")
        
        elif type is dict:
            pass

        

                
def _get_top_vendors_by_weight_lists(vendor_lifnrs, vendor_weights, top_n_percent=0.20):
    """
    Identifies the top N percent of vendors based on their corresponding weights.
    
    Args:
        vendor_lifnrs (list): List of vendor IDs (LIFNRs).
        vendor_weights (list): List of numerical weights, corresponding by index.
        top_n_percent (float): The percentage (0.0 to 1.0) of vendors to return as 'top'.

    Returns:
        list: A list of the top vendor LIFNRs.
    """
    if len(vendor_lifnrs) != len(vendor_weights):
        raise ValueError("Vendor LIFNR list and Weights list must have the same length.")

    # 1. Combine LIFNRs and Weights into a list of tuples: [(lifnr1, weight1), ...]
    combined_data = zip(vendor_lifnrs, vendor_weights)

    # 2. Sort the tuples by weight (the second element, index 1) in descending order
    # key=lambda item: item[1] tells sort to use the weight for comparison
    sorted_data = sorted(combined_data, key=lambda item: item[1], reverse=True)

    # 3. Determine how many vendors qualify as "top" (e.g., top 20%)
    total_vendors = len(sorted_data)
    num_top_vendors = max(1, int(total_vendors * top_n_percent)) # Use max(1, ...) to ensure at least one vendor is returned

    # 4. Extract just the LIFNRs for the top slice
    top_vendors_list = [item[0] for item in sorted_data[:num_top_vendors]]

    return top_vendors_list
import csv

def read_csv_rows_generator(filepath, encoding='utf-8', delimiter=',', quotechar='"', has_header=True):
    """
    Reads a CSV file row by row and yields each row as a dictionary.

    This function is memory-efficient as it does not load the entire file
    into memory at once.

    Args:
        filepath (str): The path to the CSV file.
        encoding (str): The encoding of the CSV file (default: 'utf-8').
        delimiter (str): The character used to separate fields (default: ',').
        quotechar (str): The character used to quote fields containing special
                         characters (default: '"').
        has_header (bool): If True, the first row is treated as a header
                           and subsequent rows are yielded as dictionaries
                           with header names as keys. If False, rows are
                           yielded as lists of strings.

    Yields:
        dict or list: If `has_header` is True, yields a dictionary where keys
                      are column headers and values are row data.
                      If `has_header` is False, yields a list of strings
                      representing the row data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        csv.Error: If there's an issue parsing the CSV file.
    """
    try:
        with open(filepath, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter, quotechar=quotechar)

            if has_header:
                try:
                    header = next(reader)
                except StopIteration:
                    # File is empty or only contains header if has_header is True
                    return # No data rows to yield
                
                for row_values in reader:
                    if len(row_values) != len(header):
                        # Handle malformed rows if necessary, or skip
                        # For simplicity, we'll just log and skip or raise
                        logging.warning(f"Skipping malformed row: {row_values}. Expected {len(header)} columns, got {len(row_values)}.")
                        continue
                    yield dict(zip(header, row_values))
            else:
                for row_values in reader:
                    yield row_values

    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{filepath}' was not found.")
    except csv.Error as e:
        raise csv.Error(f"Error reading CSV file '{filepath}': {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


