import sys

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import calculate_sample_size

def compute_similarity(query: str, df: pd.DataFrame, columns: []):
    """
    Compute cosine similarity between a query and a dataframe of text data
    """
    # Combine relevant text columns for vectorization
    df['combined_text'] = df[columns].fillna('').apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

    # Vectorize the text data
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(df['combined_text'])
    query_vec = vectorizer.transform([query])

    # Calculate cosine similarity between the query and all documents
    return cosine_similarity(query_vec, tfidf_matrix).flatten()


if __name__ == '__main__':
    # sys.argv.append("../data/GH_data_safetensor.csv")
    if len(sys.argv) < 2:
        print("Usage: python analyze_devs_discussion.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]

    # Load the data
    df = pd.read_csv(filename)

    # Define query and compute cosine similarity
    query = "model serialization safetensors"
    cosine_similarities = compute_similarity(query, df, ['json_content'])
    df['cosine_similarity'] = cosine_similarities

    # sort by cosine similarity (descending)
    df = df.sort_values(by='cosine_similarity', ascending=False)
    # format the dataframe columns
    df = df[['cosine_similarity', 'source', 'json_content']]
    df = df.rename(columns={'json_content': 'content'})
    df.rename_axis('id', inplace=True)
    df['is_true_positive'] = None
    df['comments'] = None

    # calculate sample size
    sample_size = calculate_sample_size(len(df), 0.95, 0.05)

    # make index start at 1
    df.index = df.index + 1

    # save only the first sample_size rows
    output_filename = filename.replace('.csv', '_sorted.csv')
    df.to_csv(output_filename, index=True)

    print(f"Samples saved to {output_filename}")
    print(f"Sample size: {sample_size}")