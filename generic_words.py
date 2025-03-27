import os
import json
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import fitz  # PyMuPDF
import os
import numpy as np

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Parameters
PDF_FOLDER = os.path.join(os.path.dirname(__file__), "materials", "GEE")
generic_words = set()
DEFAULT_PERCENTILE = 20  # Adjust this to control filtering (10-30% is typical)

def extract_text_by_page(pdf_path):
    """Extracts text from each page of a PDF separately."""
    doc = fitz.open(pdf_path)
    page_chunks = []
    
    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").strip()
        if text:
            page_chunks.append({"text": text, "page": page_num + 1})
    
    return page_chunks

def extract_text_from_files():
    """Extract text content from all text files in a directory."""
    documents = []
    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            page_chunks = extract_text_by_page(pdf_path)

            for chunk in page_chunks:
                doc_text = chunk["text"]
                documents.append(doc_text)

    return documents

def detect_generic_words(documents):
    """Detect generic words using TF-IDF."""

    # Use TF-IDF to analyze document frequency
    vectorizer = TfidfVectorizer(stop_words="english", tokenizer=custom_tokenizer)
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    idf_scores = vectorizer.idf_

    # Compute dynamic threshold using percentiles
    min_idf = np.min(idf_scores)
    max_idf = np.max(idf_scores)
    mean_idf = np.mean(idf_scores)
    threshold = np.percentile(idf_scores, DEFAULT_PERCENTILE)  # Set dynamically
    
    # If percentile-based filtering isn’t precise enough, try:
    #threshold = mean_idf - 0.5 * np.std(idf_scores)  # Mean minus half std deviation

    #print(f"IDF Stats -> Min: {min_idf:.2f}, Max: {max_idf:.2f}, Mean: {mean_idf:.2f}, Threshold: {threshold:.2f}")

    # Identify words with low IDF (common words)
    generic_words = {feature_names[i] for i, score in enumerate(idf_scores) if score < threshold}

    # Save generic words to file for reuse
    with open(os.path.join(os.path.dirname(__file__), "generic_words.json"), "w") as file:
        json.dump(list(generic_words), file)

def custom_tokenizer(text):
    """Tokenize text using spaCy and return individual words."""
    doc = nlp(text)
    tokens = [token.text for token in doc if token.pos_ in {"NOUN", "PROPN"} and not token.is_stop]
    return tokens


if __name__ == "__main__":
    documents = extract_text_from_files()
    detect_generic_words(documents)
