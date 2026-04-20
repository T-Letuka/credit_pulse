#%%
import pandas as pd
from sqlalchemy import create_engine, text

#DONT FORGET TO WRITE A CONNECTION STRING TO YOUR LOCAL SQL SERVER. 

file_path = "raw/CBM_data_Q4 2024.xlsx"

df_raw = pd.read_excel(file_path, sheet_name='CBM Data', header=None)

def extract_table(df_raw, data_start_row, data_end_row, period_row):
    # Get period labels — start from column 1, skip column 0
    periods = df_raw.iloc[period_row, 1:].values

    # Get data rows
    data = df_raw.iloc[data_start_row:data_end_row + 1, :]

    rows = []
    for _, row in data.iterrows():
        category = str(row.iloc[0]).strip()
        if not category or category == 'nan':
            continue
        for i, val in enumerate(row.iloc[1:].values):
            period = str(periods[i]).strip()
            if period == 'nan' or period == 'None':
                continue
            try:
                value = float(val)
            except (ValueError, TypeError):
                continue
            rows.append({
                'category': category,
                'period': period,
                'value': value
            })

    return pd.DataFrame(rows)

# Extract with corrected row numbers
table1 = extract_table(df_raw, data_start_row=3,  data_end_row=10, period_row=2)
table2 = extract_table(df_raw, data_start_row=16, data_end_row=23, period_row=15)
table3 = extract_table(df_raw, data_start_row=30, data_end_row=34, period_row=29)
table4 = extract_table(df_raw, data_start_row=40, data_end_row=45, period_row=39)
table8 = extract_table(df_raw, data_start_row=76, data_end_row=78, period_row=75)
table9 = extract_table(df_raw, data_start_row=84, data_end_row=86, period_row=83)


table1['source'] = 'consumer_standing'
table2['source'] = 'account_standing'
table3['source'] = 'enquiries_type'
table4['source'] = 'enquiries_sector'
table8['source'] = 'credit_reports'
table9['source'] = 'disputes'


all_periods = pd.concat([
    table1[['period']], table2[['period']], table3[['period']],
    table4[['period']], table8[['period']], table9[['period']]
]).drop_duplicates().reset_index(drop=True)


def clean_period_label(label):
    label = str(label).strip()
    # Strip all types of quotes from both ends
    for char in ['\u2018', '\u2019', '\u201c', '\u201d', "'", '"']:
        label = label.replace(char, "'")
    # Remove spaces before year e.g. "Dec '24" -> "Dec'24"
    label = label.replace(" '", "'")
    # Fix "June" -> "Jun"
    label = label.replace("June", "Jun")
    return label

# Parse month and year from period label e.g. "Jun'07"
month_map = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}



def parse_period(label):
    label = clean_period_label(label)
    mon_str = label[:3]
    yr_str = label[4:].strip()  # skip the quote character at index 3
    month = month_map.get(mon_str, None)
    year = int("20" + yr_str) if int(yr_str) < 50 else int("19" + yr_str)
    quarter = f"Q{(month - 1) // 3 + 1}"
    return month, year, quarter

# Also clean the period column itself before lookup
all_periods['period'] = all_periods['period'].apply(clean_period_label)
all_periods = all_periods.drop_duplicates(subset=['period']).reset_index(drop=True)
all_periods[['month', 'year', 'quarter']] = all_periods['period'].apply(
    lambda x: pd.Series(parse_period(x))
)
all_periods = all_periods.sort_values(['year', 'month']).reset_index(drop=True)
all_periods.insert(0, 'period_id', all_periods.index + 1)
all_periods.rename(columns={'period': 'period_label'}, inplace=True)

# --- LOAD dim_period ---
with engine.connect() as conn:
    conn.execute(text("DELETE FROM dim_period"))
    conn.commit()

all_periods.to_sql('dim_period', con=engine, if_exists='append', index=False)
print(f"dim_period loaded — {len(all_periods)} rows")

# --- HELPER TO LOAD FACT TABLES ---
period_lookup = all_periods.set_index('period_label')['period_id'].to_dict()

def load_fact_table(df, table_name, value_col='value', include_source=False,delete_first=True):
    df = df.copy()
    df['period'] = df['period'].apply(clean_period_label)
    df['period_id'] = df['period'].map(period_lookup)
    missing = df['period_id'].isna().sum()
    if missing > 0:
        print(f"  WARNING: {missing} rows had unmatched periods and will be skipped")
    df = df.dropna(subset=['period_id'])
    df['period_id'] = df['period_id'].astype(int)
    df = df.rename(columns={'value': value_col})

    if include_source:
        cols = ['period_id', 'source', 'category', value_col]
    else:
        cols = ['period_id', 'category', value_col]

    df = df[cols]

    if delete_first:
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()

    df.to_sql(table_name, con=engine, if_exists='append', index=False)
    print(f"{table_name} loaded — {len(df)} rows")

# --- LOAD ALL FACT TABLES ---

load_fact_table(table1, 'fact_consumer_standing', value_col='value_millions', include_source=False)
load_fact_table(table2, 'fact_account_standing',  value_col='value_millions', include_source=False)

print("\nAll tables loaded successfully 🔥")



#%%

# %%
with engine.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    conn.execute(text("DELETE FROM fact_consumer_standing"))
    conn.execute(text("DELETE FROM fact_account_standing"))
    conn.execute(text("DELETE FROM fact_enquries"))
    conn.execute(text("DELETE FROM fact_disputes_reports"))
    conn.execute(text("DELETE FROM dim_period"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    conn.commit()

print("All tables cleared")

# %%
load_fact_table(table3, 'fact_enquries',          value_col='value',         include_source=True)
load_fact_table(table4, 'fact_enquries',          value_col='value',         include_source=True)
load_fact_table(table8, 'fact_disputes_reports',   value_col='value',         include_source=True)
load_fact_table(table9, 'fact_disputes_reports',   value_col='value',         include_source=True)

# %%
