import os
import zipfile
from pathlib import Path

import pandas as pd
import json
from nb_utils import unzip, DATA_DIR

# Extracted results, load to frame and delete the large CSV
unzip(DATA_DIR / 'sfconvertbot_pr_metadata.csv.zip', DATA_DIR)
df1 = pd.read_csv(Path('../../data/sfconvertbot_pr_metadata.csv'))
os.remove(DATA_DIR / 'sfconvertbot_pr_metadata.csv')
df2 = pd.read_csv(Path('../../data/hf_conversions.csv'))
# fix timestamps to make it consistent across datasets
for index, row in df2.iterrows():
    pr_url = row['pr_url'].split("#")[0]
    header = row['header_metadata'] if row['header_metadata'] else ""
    json_header = json.loads(row['header_metadata']) if header.startswith('{') else None
    df2.loc[index,'time'] = json_header['discussion']['createdAt'] if json_header else None
# drop duplicates from df2
df2.drop_duplicates(subset='pr_url', inplace=True)

# exclude from df2 pr_url that are in df
df3 = df1.copy()
df3['pr_url'] = df1['pr_url'].str.split('#').str[0].str.strip()
df2 = df2[~df2['pr_url'].isin(df3['pr_url'])]
# merge the two dataframes together based on the pr_url
df4 = pd.concat([df1, df2], ignore_index=True)
# drop duplicates
df4 = df4.drop_duplicates(subset='pr_url')
# # save new results
# df4.to_csv(DATA_DIR / 'NEW_sfconvertbot_pr_metadata.csv', index=False)
# # zip it
# with zipfile.ZipFile(DATA_DIR / 'sfconvertbot_pr_metadata.csv.zip', 'w') as zf:
#     zf.write(DATA_DIR / 'sfconvertbot_pr_metadata.csv', 'sfconvertbot_pr_metadata.csv')
#
# # remove the csv
# os.remove(DATA_DIR / 'NEW_sfconvertbot_pr_metadata.csv')
print(len(df1), len(df2), len(df4), len(df4.drop_duplicates(subset='pr_url')))