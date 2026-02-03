import pandas as pd

def compare_excel_files(file1,file2, output_csv, sheet1_name=0,sheet2_name=0):
    # Read Excel files
    df1 = pd.read_excel(file1, sheet_name=sheet1_name)
    df2 = pd.read_excel(file2, sheet_name=sheet2_name)

    # Align both DataFrames (handles different shapes)
    df1, df2 = df1.align(df2, join="outer", axis=1)
    df1, df2 = df1.align(df2, join="outer", axis=0)

    differences = []

    for row in range(len(df1)):
        for col in df1.columns:
            val1 = df1.at[row, col]
            val2 = df2.at[row, col]

            # Treat NaN == NaN as equal
            if pd.isna(val1) and pd.isna(val2):
                continue

            if val1 != val2:
                differences.append({
                    "Row": row + 2,  # +2 to account for header & 0-index
                    "Column": col,
                    "File1_Value": val1,
                    "File2_Value": val2
                })

    # Save differences to CSV
    diff_df = pd.DataFrame(differences)
    diff_df.to_csv(output_csv, index=False)

    print(f"Comparison complete. {len(diff_df)} differences saved to {output_csv}")

# Example usage
compare_excel_files(
    file1="../Fairness-Metrics.xlsx",
    file2="../Fairness-Metrics.xlsx",
    output_csv="differences.csv",
    sheet1_name="METRICS",  # can be sheet name or index
    sheet2_name="(Ont) Metrics"
)