import pandas as pd

def process_excel(input_file, output_file):
    """
    Process an Excel file with multiple sheets and convert each sheet into a standardized format.
    
    Args:
    input_file (str): Path to the input Excel file.
    output_file (str): Path to save the cleaned Excel file.
    """
    # Load the Excel file
    sheets = pd.ExcelFile(input_file)
    
    # Initialize a dictionary to store the processed data for each sheet
    processed_sheets = {}

    # Process each sheet
    for sheet_name in sheets.sheet_names:
        df = sheets.parse(sheet_name)
        
        # Melt the DataFrame to unpivot time columns into rows
        df_melted = df.melt(id_vars=[df.columns[0]], var_name="Time", value_name="Scheduled")
        
        # Filter to include only rows where "Scheduled" is not empty or 0
        df_filtered = df_melted[df_melted["Scheduled"].notnull() & (df_melted["Scheduled"] != 0)]
        
        # Keep only the Task and Time columns
        df_result = df_filtered[[df.columns[0], "Time"]]
        df_result.columns = ["Task", "Time"]
        
        # Store the cleaned data
        processed_sheets[sheet_name] = df_result

    # Save the cleaned data back into a new Excel file
    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, df_result in processed_sheets.items():
            df_result.to_excel(writer, sheet_name=sheet_name, index=False)

if __name__ == "__main__":
    # Define the input and output file paths
    input_file = "NW example.xlsx"  # Replace with your input file path
    output_file = "Cleaned_NW_Schedule.xlsx"  # Replace with your desired output file path

    # Process the file
    process_excel(input_file, output_file)
    print(f"Processed file saved as {output_file}")
