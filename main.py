import os
import PyPDF2
from docx import Document
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import streamlit as st
from collections import Counter
from math import sqrt

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
        return text

def read_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + " "
    return text

def read_stop_words_sastrawi():
    stopword_factory = StopWordRemoverFactory()
    return stopword_factory.get_stop_words()

def read_dicti_sastrawi(file_path):
    dicti = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                dicti[parts[0]] = parts[1]
            # else:
                # print(f"Ignoring invalid line: {line}")
    return dicti

def preprocess_text(text, stop_words, dicti):
    text_lower = text.lower()
    text_cleaned = ''.join(char for char in text_lower if char.isalpha() or char.isspace())
    tokens = text_cleaned.split()
    filtered_tokens = [token for token in tokens if token not in stop_words]
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    stemmed_tokens = [stemmer.stem(token) if token not in dicti else dicti[token] for token in filtered_tokens]

    return text_lower, text_cleaned, tokens, stemmed_tokens

def preprocess_directory(directory_path, stop_words, dicti):
    results = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if file_path.endswith(".txt"):
            content = read_txt(file_path)
        elif file_path.endswith(".pdf"):
            content = read_pdf(file_path)
        elif file_path.endswith(".docx"):
            content = read_docx(file_path)
        else:
            print(f"Ignoring unsupported file: {file_path}")
            continue

        original_lower, original_cleaned, original_tokens, stemmed_tokens = preprocess_text(content, stop_words, dicti)
        word_count = len(stemmed_tokens)
        results.append((filename, content, original_lower, original_cleaned, original_tokens, stemmed_tokens, word_count))
    return results

def calculate_similarity(query, documents, stop_words, dicti, all_words):
    query_stemmed_tokens = preprocess_text(query, stop_words, dicti)[3]
    query_vector = build_doc_vector(Counter(query_stemmed_tokens), all_words)
    document_vectors = [build_doc_vector(Counter(doc), all_words) for _, _, _, _, _, doc, _ in documents]
    similarity_scores = [cosine_similarity(query_vector, doc_vector) for doc_vector in document_vectors]
    return similarity_scores

def build_doc_vector(doc, all_words):
    doc_vector = [doc.get(word, 0) for word in all_words]
    return doc_vector

def cosine_similarity(vec1, vec2):
    dot_product = sum(x * y for x, y in zip(vec1, vec2))
    magnitude_vec1 = sqrt(sum(x**2 for x in vec1))
    magnitude_vec2 = sqrt(sum(x**2 for x in vec2))
    
    if magnitude_vec1 == 0 or magnitude_vec2 == 0:
        return 0
    
    return dot_product / (magnitude_vec1 * magnitude_vec2)

def calculate_unique_vector(docs):
    all_words = set(word for _, _, _, _, _, doc, _ in docs for word in doc)
    sorted_all_words = sorted(all_words)
    return list(sorted_all_words)

def print_matrix(matrix, header=None):
    if header:
        print("\t".join(header))
    for row in matrix:
        print("\t".join(str(value) for value in row))

def word_count_table(stemmed_tokens):
    word_counts = Counter(stemmed_tokens)
    data = {'Word': [], 'Count': []}
    for word, count in word_counts.items():
        data['Word'].append(word)
        data['Count'].append(count)
    return data

if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False

def callback():
    st.session_state.button_clicked = True

def open_file(file_path):
    try:
        os.startfile(file_path)  
        st.success('File successfully opened')
    except:
        st.warning('An error occurred while opening the file')

def main():
    st.header('Implementing the :orange[VSM] (Vector Space Model) Algorithm for Information Retrieval', divider='orange')

    path_option = st.radio("Select Path Option:", ["Use Current Path", "Enter Path Manually"])

    if path_option == "Use Current Path":
        directory_path = "file_test_dicky"
    else:
        directory_path = st.text_input("Enter the directory path:")

    if directory_path and os.path.exists(directory_path):
        stop_words = read_stop_words_sastrawi()
        dicti = read_dicti_sastrawi("kata-dasar.txt")

        st.subheader("List of Files in the Directory:")
        file_list = os.listdir(directory_path)
        st.text("\n".join(file_list))

        results = preprocess_directory(directory_path, stop_words, dicti)

        st.subheader("Results:")
        st.header('', divider='orange')  
        for filename, content, original_lower, original_cleaned, original_tokens, stemmed_tokens, word_count in results:
            st.subheader(f"**File:** :orange[{filename}]")
            st.write("**Original Content:**", content)
            st.write("**After Case Folding:**", f":orange[{original_lower}]")
            st.write("**After Cleaned:**", f":orange[{original_cleaned}]")
            st.write("**After Tokenize:**", original_tokens)
            st.write("**After Stemmed:**", stemmed_tokens)
            st.write(f"**Total Words:** {word_count}")
            st.write("Word Count Table:")
            word_count_data = word_count_table(stemmed_tokens)
            st.table(word_count_data)

            st.header('', divider='orange')  

        all_words = calculate_unique_vector(results)
        st.subheader("Vector Unique Word:")
        st.table([all_words])
        st.header('', divider='orange')  

        st.subheader("Query:")
        user_query = st.text_input("Enter your query:")

        if st.button("Search", on_click=callback) or st.session_state.button_clicked:
            if user_query:
                similarity_scores = calculate_similarity(user_query, results, stop_words, dicti, all_words)

                st.subheader("Search Results:")
                for (filename, _, _, _, _, _, _), score in sorted(zip(results, similarity_scores), key=lambda x: x[1], reverse=True):
                    st.write(f"**Similarity Score** :orange[{filename}] : :red[{score:.4f}]")
                    if st.button(f"Open :orange[{filename}]", key=str(filename)):
                        file_path = os.path.join(directory_path, filename)
                        open_file(file_path)
    elif directory_path:
        st.warning("Directory does not exist.")

    st.markdown("---")

if __name__ == "__main__":
    main()