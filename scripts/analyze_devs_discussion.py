import sys

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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
    sys.argv.append('../data/GH_data_safetensor.csv')
    if len(sys.argv) < 2:
        print("Usage: python analyze_devs_discussion.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]

    df = pd.read_csv(filename)
    query = "model serialization safetensors"
    cosine_similarities = compute_similarity(query, df, ['json content'])
    df['cosine_similarity'] = cosine_similarities

    # sort by cosine similarity (descending)
    df = df.sort_values(by='cosine_similarity', ascending=False)
    # keep only the headers source, and json_content
    df = df[['cosine_similarity', 'source', 'json content']]
    # rename json content to content
    df = df.rename(columns={'json content': 'content'})
    df['is_true_positive'] = None
    df['comments'] = None
    df.to_csv(filename.replace(".csv", "_similarities.csv"), index=False)
