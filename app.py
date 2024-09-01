# import streamlit as st
# from PyPDF2 import PdfReader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# import os
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# import google.generativeai as genai
# from langchain.vectorstores import FAISS
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.chains.question_answering import load_qa_chain
# from langchain.prompts import PromptTemplate
# from dotenv import load_dotenv

# load_dotenv()
# os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))






# def get_pdf_text(pdf_docs):
#     text=""
#     for pdf in pdf_docs:
#         pdf_reader= PdfReader(pdf)
#         for page in pdf_reader.pages:
#             text+= page.extract_text()
#     return  text



# def get_text_chunks(text):
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
#     chunks = text_splitter.split_text(text)
#     return chunks


# def get_vector_store(text_chunks):
#     embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
#     vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
#     vector_store.save_local("faiss_index")


# def get_conversational_chain():

#     prompt_template = """
#     Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
#     provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
#     Context:\n {context}?\n
#     Question: \n{question}\n

#     Answer:
#     """

#     model = ChatGoogleGenerativeAI(model="gemini-pro",
#                              temperature=0.3)

#     prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
#     chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

#     return chain



# def user_input(user_question):
#     embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
#     new_db = FAISS.load_local("faiss_index", embeddings)
#     docs = new_db.similarity_search(user_question)

#     chain = get_conversational_chain()

    
#     response = chain(
#         {"input_documents":docs, "question": user_question}
#         , return_only_outputs=True)

#     print(response)
#     st.write("Reply: ", response["output_text"])




# def main():
#     st.set_page_config("Conference Summarizer")
#     st.header("Chat with your personal assistant 💁")

#     user_question = st.text_input("Ask a Question from based on your office meetings, conferences and much more. ")

#     if user_question:
#         user_input(user_question)

#     with st.sidebar:
#         st.title("Menu:")
#         pdf_docs = st.file_uploader("Upload your meeting documents and resources and Click on the Submit & Process Button", accept_multiple_files=True)
#         if st.button("Submit & Process"):
#             with st.spinner("Processing..."):
#                 raw_text = get_pdf_text(pdf_docs)
#                 text_chunks = get_text_chunks(raw_text)
#                 get_vector_store(text_chunks)
#                 st.success("Done")



# if __name__ == "__main__":
#     main()


import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from gensim import corpora
from gensim.models import LdaModel
from gensim.parsing.preprocessing import STOPWORDS
import matplotlib.pyplot as plt
from googletrans import Translator
import speech_recognition as sr
import pyttsx3
from fpdf import FPDF

# Download necessary NLTK data
nltk.download('vader_lexicon')

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    st.write("Reply: ", response["output_text"])

def sentiment_analysis(text):
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(text)
    return sentiment

def extract_action_items(text):
    # Simple rule-based action item extraction
    sentences = text.split('.')
    action_items = [s.strip() for s in sentences if 'action item' in s.lower() or 'todo' in s.lower()]
    return action_items

def topic_modeling(text):
    texts = [text.lower().split()]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=3, random_state=100, update_every=1, chunksize=100, passes=10, alpha='auto', per_word_topics=True)
    return lda_model.print_topics()

def translate_text(text, target_language='en'):
    translator = Translator()
    translated = translator.translate(text, dest=target_language)
    return translated.text

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Speak now...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.write("Could not understand audio")
    except sr.RequestError:
        st.write("Could not request results; check your network connection")

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def generate_meeting_minutes(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output("meeting_minutes.pdf")

def main():
    st.set_page_config("Enhanced Conference Summarizer")
    st.header("Chat with your personal assistant 💁")

    user_question = st.text_input("Ask a Question based on your office meetings, conferences and much more.")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your meeting documents and resources and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")

        st.subheader("Additional Features")
        if st.button("Analyze Sentiment"):
            sentiment = sentiment_analysis(raw_text)
            st.write(f"Sentiment: {sentiment}")

        if st.button("Extract Action Items"):
            action_items = extract_action_items(raw_text)
            st.write("Action Items:", action_items)

        if st.button("Generate Topic Model"):
            topics = topic_modeling(raw_text)
            st.write("Topics:", topics)

        target_lang = st.selectbox("Select language for translation", ['en', 'es', 'fr', 'de', 'it'])
        if st.button("Translate"):
            translated_text = translate_text(raw_text, target_lang)
            st.write("Translated Text:", translated_text)

        if st.button("Voice Input"):
            spoken_text = speech_to_text()
            st.write("You said:", spoken_text)

        if st.button("Text-to-Speech"):
            text_to_speech(raw_text)
            st.write("Audio played")

        if st.button("Generate Meeting Minutes"):
            generate_meeting_minutes(raw_text)
            st.write("Meeting minutes generated and saved as 'meeting_minutes.pdf'")

if __name__ == "__main__":
    main()