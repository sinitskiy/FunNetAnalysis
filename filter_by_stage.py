import pandas as pd


df = pd.read_csv('./wd/unambiguous_file_metadata_with_urls.csv')

# Print unique values from the "tumor_stage" column
print("Unique values in 'tumor_stage':", df['tumor_stage'].unique())

# Filter rows for non-invasive tumors
filtered_data = df[df['tumor_stage'].isin(['Stage I', 'Stage1'])]
print(f"Found {len(filtered_data)} non-invasive datapoints")
filtered_data.to_csv('data_noninvasive.csv', index=False)

# Filter rows for invasive tumors
filtered_data = df[df['tumor_stage'].str.startswith('Stage III', na=False)]
filtered_data.to_csv('data_invasive.csv', index=False)
print(f"Found {len(filtered_data)} invasive datapoints")
