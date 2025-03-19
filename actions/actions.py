import sys
sys.modules["sqlite3"] = __import__("pysqlite3")
import chromadb
import numpy as np
import google.generativeai as genai
from rasa_sdk import Action, Tracker
from sentence_transformers import SentenceTransformer
import os
from rasa_sdk.events import SlotSet, FollowupAction
from typing import Any, Text, Dict, List
from rasa_sdk.executor import CollectingDispatcher

from .utils import *

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Set up Google Gemini API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Connect to ChromaDB
VECTOR_DB_PATH = "vector_store"
chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = chroma_client.get_collection(name="class_materials")

# === ACTION 1: FETCH RAW MATERIAL === #
class ActionFetchClassMaterial(Action):
    def name(self):
        return "action_fetch_class_material"

    def run(self, dispatcher, tracker, domain):

        user_message = tracker.latest_message.get("text")
        sender_id = tracker.sender_id  # ✅ Retrieves the "sender" field
        #metadata_email = tracker.latest_message.get("metadata", {}).get("user_email")

        print(f"\n🧒 User ({sender_id}) said: {user_message} 📩")
        query = treat_raw_query(user_message)

        # === DENSE (Vector) SEARCH === #
        print(f"\n🔛 Getting query embeddings for query: '{query}'\n...")
        
        query_embedding = model.encode(query, convert_to_numpy=True).tolist()
        vector_results = collection.query(query_embeddings=[query_embedding], n_results=20)

        vector_docs = vector_results["documents"][0]
        vector_metadata = vector_results["metadatas"][0]
        vector_scores = vector_results["distances"][0]  # Lower is better (L2 distance)


        # === Perform Hyvrid BM25 search === #
        print(f"\n🔛 Getting BM25 sparse vectors...")

        # Step 1: Extract both complex & simple tokens
        complex_tokens = extract_complex_tokens(query)  # e.g., ["pestel analysis"]
        simple_tokens = extract_simple_tokens(query)  # e.g., ["pestel", "analysis"]
        print(f"📖 Finding material location for:\n - {complex_tokens}\n - {simple_tokens}")

        # Step 3: Expand using **weighted synonyms** (prefer closer meanings)
        expanded_complex = expand_query_with_weighted_synonyms(complex_tokens)
        expanded_simple = expand_query_with_weighted_synonyms(simple_tokens)
        print(f"🔄 Expanded tokens with synonyms:\n - {expanded_complex}\n - {expanded_simple}")

        specific_terms = [word for word in expanded_simple if not is_common_word(word)]
        generic_terms = [word for word in expanded_simple if is_common_word(word)]

        print(f"\n🔍 Specific terms: {specific_terms}")
        print(f"📌 Generic terms: {generic_terms}")

        print(f"    🔛 Getting BM25 sparse vectors for both:\n - {expanded_complex}\n - {specific_terms}")
        

        # Step 4: Perform BM25 Search
        bm25_scores_complex = bm25_index.get_scores(expanded_complex)
        bm25_scores_simple = bm25_index.get_scores(specific_terms)

        # Step 5: Combine Scores (Weighting Complex Matches Higher)
        final_scores = 1.5 * bm25_scores_complex + 1.0 * bm25_scores_simple  # Give priority to complex matches
        top_bm25_indices = np.argsort(final_scores)[::-1][:20]  # Top 20 results

        bm25_docs = [bm25_documents[i] for i in top_bm25_indices]
        bm25_metadata_selected = [bm25_metadata[i] for i in top_bm25_indices]
        bm25_scores_selected = [final_scores[i] for i in top_bm25_indices]


        # === NORMALIZE SCORES === #
        max_vec_score = max(vector_scores) if vector_scores else 1
        vector_scores = [1 - (score / max_vec_score) for score in vector_scores]  # Convert L2 to similarity

        # === NORMALIZE SCORES === #
        max_bm25_score = max(bm25_scores_selected) if bm25_scores_selected else 1  # Avoid division by zero
        if max_bm25_score > 0:
            bm25_scores_selected = [score / max_bm25_score for score in bm25_scores_selected]  # Normalize BM25 scores
        else:
            print("⚠️ Warning: max_bm25_score is zero. Normalization will be skipped.")


        # === MERGE & RE-RANK RESULTS === #
        hybrid_results = []
        alpha = 0.7  # Balance factor between vector & keyword search

        for doc, meta, score in zip(vector_docs, vector_metadata, vector_scores):
            hybrid_score = alpha * score
            hybrid_results.append((doc, meta, hybrid_score))

        for doc, meta, score in zip(bm25_docs, bm25_metadata_selected, bm25_scores_selected):
            hybrid_score = (1 - alpha) * score 
            hybrid_results.append((doc, meta, hybrid_score))

        # Sort results by hybrid score
        hybrid_results = sorted(hybrid_results, key=lambda x: x[2], reverse=True)

        # === ADAPTIVE THRESHOLDING BASED ON PERCENTILE === #
        scores = [score for _, _, score in hybrid_results]
        max_score = max(scores) if scores else 1
        adaptive_threshold = max(np.mean(scores) + 0.5 * np.std(scores), np.percentile(scores, 80), 0.7 * max_score)
        print(f"\n📊 Adaptive Threshold: {np.mean(scores) + 0.5 * np.std(scores):.3f}, Percentile_80 threshold: {np.percentile(scores, 80):.3f}, Max Score Threshold: {0.7 * max_score:.3f} \nFinal Threshold => {adaptive_threshold:.3f}")

        # Filter results
        selected_results = [(doc, meta, score) for doc, meta, score in hybrid_results if score >= adaptive_threshold]

        if len(selected_results) == 0:
            dispatcher.utter_message(text="I couldn't find relevant class materials for your query.")
            print("\n🚨 No relevant materials found!")
            gemini_results = []
        else: 
            print("\n✅ Selected Pages After Filtering:")
            document_entries = []
            pdf_insights = []
            idx = 1
            for doc, meta, score in selected_results:
                pdf_insights.append(meta['file'])
                document_entries.append((meta['file'], meta['page']))
                print(f"{idx}. 📄 PDF: {meta['file']} | Page: {meta['page']} | Score: {score:.4f}")
                idx += 1
            
            # stay only with unique pdfs
            pdf_insights = list(set(pdf_insights))

            # **Sort by PDF name (A-Z) and then by page number (ascending)**
            document_entries.sort(key=lambda x: (x[0].lower(), x[1]))
            gemini_results = group_pages_by_pdf(document_entries)  

            # Format results
            results_text = []
            for text_chunk, meta, score in selected_results:
                file_name = meta["file"]
                page_number = meta["page"]
                results_text.append(f"📄 **From {file_name} (Page {page_number})**:\n{text_chunk}")

            # === PREPARE QUERY FOR GEMINI === #
            raw_text = "\n".join(results_text)
            prompt = f"Use the following raw educational content to answer the student query: '{query}'. Make the provided content more readable to the student: \n{raw_text} "

            print("\n📢 Sending to Gemini API for Summarization...")
            #print(f"🔹 Prompt: {prompt[:200]}\n")  # Show only first 200 chars for readability
            
            formatted_response = "Sorry, I couldn't generate a response..."
            try:
                g_model = genai.GenerativeModel("gemini-1.5-pro-latest")
                response = g_model.generate_content(prompt)

                if hasattr(response, "text") and response.text:
                    print("\n🎯 Gemini Response Generated Successfully!")
                    formatted_response = format_gemini_response(response.text)
                    print(formatted_response)
                    dispatcher.utter_message(text=formatted_response)
                else:
                    print("\n⚠️ Gemini Response is empty.")
                    dispatcher.utter_message(text="Sorry, I couldn't generate a response.")
            except Exception as e:
                dispatcher.utter_message(text="Sorry, I couldn't process that request.")
                print(f"\n❌ Error calling Gemini API: {e}")

        return  [
            SlotSet("user_query", query),  # Store the query
            SlotSet("materials_location", gemini_results),  # Store selected materials
            SlotSet("bot_response", formatted_response),  # Store the bot response
            SlotSet("sender_id", sender_id),  # Store the sender ID
            SlotSet("pdfs", pdf_insights)  # Store the pdf insights
            ]


# === ACTION 2: GET PDF NAMES & PAGE LOCATIONS === #
class ActionGetClassMaterialLocation(Action):
    def name(self):
        return "action_get_class_material_location"

    def run(self, dispatcher, tracker, domain):

        selected_materials = tracker.get_slot("materials_location")
        bot_response = tracker.get_slot("bot_response")
        sender_id = tracker.get_slot("sender_id")
        pdfs = tracker.get_slot("pdfs")
        query = tracker.get_slot("user_query") # already treated in last function

        print(f"\n\n 🔖 --------- Getting class materials location --------- 🔖 ")

        # === Perform Hyvrid BM25 search === #
        # Step 1: Extract both complex & simple tokens
        complex_tokens = extract_complex_tokens(query)  # e.g., ["pestel analysis"]
        simple_tokens = extract_simple_tokens(query)  # e.g., ["pestel", "analysis"]
        print(f"\n📖📖 Finding material location for:\n - {complex_tokens}\n - {simple_tokens}")

        # Step 3: Expand using **weighted synonyms** (prefer closer meanings)
        expanded_complex = expand_query_with_weighted_synonyms(complex_tokens)
        expanded_simple = expand_query_with_weighted_synonyms(simple_tokens)
        print(f"🔄 Expanded tokens with synonyms:\n - {expanded_complex}\n - {expanded_simple}")
        
        # Step 4: Perform BM25 Search
        bm25_scores_complex = bm25_index.get_scores(expanded_complex)
        bm25_scores_simple = bm25_index.get_scores(expanded_simple)

        # Step 5: Combine Scores (Weighting Complex Matches Higher)
        final_scores = 1.5 * bm25_scores_complex + 1.0 * bm25_scores_simple  # Give priority to complex matches

        top_indices = np.argsort(final_scores)[::-1][:10]  # Top 10 results

        specific_terms = [word for word in expanded_simple if not is_common_word(word)]
        generic_terms = [word for word in expanded_simple if is_common_word(word)]

        print(f"\n🔍 Specific terms: {specific_terms}")
        print(f"📌 Generic terms: {generic_terms}")
    

        location_results = []
        document_entries = []  # Store documents before sorting
        pdfs_insights = []

        for i in top_indices:
            file_name = bm25_metadata[i]["file"]
            page_number = bm25_metadata[i]["page"]
            document_text = bm25_documents[i]

            # Tokenize the document text
            document_tokens = extract_complex_tokens(document_text)

            # Perform fuzzy matching -> solves matches like 'external environment analysis\npestel analysis'
            if fuzzy_match(expanded_complex, document_tokens):
                pdfs_insights.append(file_name)
                document_entries.append((file_name, page_number))

        if len(document_entries) == 0:
            print("\n👻 --> No matching for Complex Tokens")

            for i in top_indices:
                file_name = bm25_metadata[i]["file"]
                page_number = bm25_metadata[i]["page"]
                document_text = bm25_documents[i]
                
                # Tokenize the document text
                simple_document_tokens = extract_simple_tokens(document_text)

                # ✅ Ensure at least one "specific" word is found before allowing generic matches
                contains_specific = any(fuzzy_match([word], simple_document_tokens) for word in specific_terms)
                contains_generic = any(fuzzy_match([word], simple_document_tokens) for word in generic_terms)

                if contains_specific or (contains_generic and len(specific_terms) == 0):
                    pdfs_insights.append(file_name)
                    document_entries.append((file_name, page_number))
                
        pdfs_insights = list(set(pdfs_insights))

        # **Sort by PDF name (A-Z) and then by page number (ascending)**
        document_entries.sort(key=lambda x: (x[0].lower(), x[1]))  

        # Format results
        location_results = group_pages_by_pdf(document_entries)

        if location_results:

            if len(document_entries) > len(selected_materials) * 3: # means that the tokenization went wrong
                print("\n👻 --> Tokenization went wrong, using pdfs from slot")
                location_results = selected_materials
                save_student_progress(sender_id, query, bot_response, simple_tokens, ", ".join(pdfs))
            else:
                save_student_progress(sender_id, query, bot_response, simple_tokens, ", ".join(pdfs_insights))

            print("\n🎯 Material location for query found!")
            print("\n📌 FINAL SORTED RESULTS:")
            for result in location_results:
                print(result)
            print()

            dispatcher.utter_message(text="You can find more information in:\n" + "\n".join(location_results))
        else:
            print("\n⚠️  No exact references found, but you might check related PDFs.")
            dispatcher.utter_message(text="I couldn't find specific page references, but check related PDFs.")

        #clear the slots
        return [SlotSet("materials_location", []), SlotSet("bot_response", []), SlotSet("sender_id", ""), SlotSet("pdfs", []), SlotSet("user_query", "")]
