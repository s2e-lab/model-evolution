"""
This script formats the converter discussions data such that it is in a standardized format.
The script reads the data from a CSV file, processes it, and saves it to a new CSV file.
@Author: Joanna C. S. Santos
"""

import pandas as pd
import numpy as np
import os
import re
import json
if __name__ == '__main__':
    df = pd.read_csv('../../data/converter_discussions.csv')
    df['source'] = 'Converter Discussions'

    for index, row in df.iterrows():
        header = row['header']
        json_header = json.loads(header)
        df.at[index, 'title'] = json_header['discussion']['title']
        df.at[index, 'is_true_positive'] = 1
        df.at[index, 'comments'] = None
        df.at[index, 'id'] = index + 8000
        df.at[index, 'cosine_similarity'] = None
        df.at[index, 'content'] = row['events']

    # make is_true_positive an integer
    df['is_true_positive'] = df['is_true_positive'].astype(int)
    df['id'] = df['id'].astype(int)

    # slice frame to keep only these columns in this order id, source, content, is_true_positive, comments, cosine_similarity
    df = df[['id', 'source', 'content', 'is_true_positive', 'comments', 'cosine_similarity']]
    df.to_csv('../../data/converter_discussions_sorted.csv', index=False)