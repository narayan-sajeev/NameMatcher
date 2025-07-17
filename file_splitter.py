#!/usr/bin/env python3
"""
File splitting utilities for large output files.
"""

import math


def split_results(df, max_rows_per_file=10000, base_filename='customer_reconciliation'):
    """
    Split a large DataFrame into multiple CSV files if needed.
    
    Args:
        df: DataFrame to split
        max_rows_per_file: Maximum rows per output file
        base_filename: Base name for output files (without extension)
    
    Returns:
        List of output filenames
    """
    import csv
    
    total_rows = len(df)
    
    if total_rows <= max_rows_per_file:
        # Single file is sufficient
        filename = f"{base_filename}.csv"
        df.to_csv(filename, index=False, quoting=csv.QUOTE_ALL)
        return [filename]
    
    # Calculate number of files needed
    num_files = math.ceil(total_rows / max_rows_per_file)
    output_files = []
    
    for i in range(num_files):
        start_idx = i * max_rows_per_file
        end_idx = min((i + 1) * max_rows_per_file, total_rows)
        
        # Create filename with part number
        if num_files > 1:
            filename = f"{base_filename}_part_{i+1}_of_{num_files}.csv"
        else:
            filename = f"{base_filename}.csv"
        
        # Save the slice with proper quote handling
        df.iloc[start_idx:end_idx].to_csv(filename, index=False, quoting=csv.QUOTE_ALL)
        output_files.append(filename)
        
        print(f"  Wrote rows {start_idx+1}-{end_idx} to {filename}")
    
    return output_files
