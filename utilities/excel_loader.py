import pandas as pd

def load_excel_sheet(file,sheet_name=0):
    # Read Excel files
    df1 = pd.read_excel(file, sheet_name=sheet_name)
    
    #for row in range(5):
    #    for col in df1.columns:
    #        print(df1.at[row, col])
    #    print("\n")

    
    #print(f"Comparison complete. {len(diff_df)} differences saved to {output_csv}")

# Example usage
load_excel_sheet(
    file="../Fairness-Metrics.xlsx",
    sheet_name="METRICS"  # can be sheet name or index
)