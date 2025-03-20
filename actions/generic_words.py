import os
import json
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import fitz  # PyMuPDF
import os

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Parameters
MIN_IDF_THRESHOLD = 4  # Minimum IDF score to consider a word as specific (Tune this value as needed)
PDF_FOLDER = os.path.join(os.path.dirname(__file__), "materials", "GEE_pdfs")
generic_words = set()

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

    print(f"\nmin idf: {min(idf_scores)}")
    print(f"max idf: {max(idf_scores)}")
    print(f"mean idf: {sum(idf_scores) / len(idf_scores)}")

    # Identify words with low IDF (common words)
    generic_words = {feature_names[i] for i, score in enumerate(idf_scores) if score < MIN_IDF_THRESHOLD}  


    # Save generic words to file for reuse
    with open(os.path.join(os.path.dirname(__file__), "generic_words.json"), "w") as file:
        json.dump(list(generic_words), file)

def custom_tokenizer(text):
    """Tokenize text using spaCy and return individual words."""
    doc = nlp(text)
    tokens = [token.text for token in doc if token.pos_ in {"NOUN", "PROPN"} and not token.is_stop]
    return tokens

documents = extract_text_from_files()
detect_generic_words(documents)
