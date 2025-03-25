from langdetect import detect
from deep_translator import GoogleTranslator
import streamlit as st
import os
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from airtable_loader import fetch_airtable_data
from dotenv import load_dotenv
from jinja2 import Template
from xhtml2pdf import pisa
from datetime import date

# Load environment variables
load_dotenv()

# Streamlit setup
st.set_page_config(page_title="AI Concierge Agent", layout="centered")
st.title("🤖 My Paris Concierge – AI Assistant")

# PDF generation function
def generate_proposal_pdf(client_name, client_request, recommendation, price):
    with open("invoice_template.html") as file:
        template = Template(file.read())
    rendered_html = template.render(
        client_name=client_name,
        client_request=client_request,
        recommendation=recommendation,
        price=price,
        date=str(date.today())
    )
    output_path = "proposal.pdf"
    with open(output_path, "w+b") as f:
        pisa.CreatePDF(rendered_html, dest=f)
    return output_path

# User input
user_input = st.text_area("Paste a client request here (email-style):", height=200)

if st.button("Get AI Recommendations") and user_input:
    with st.spinner("Contacting your AI concierge..."):
        # Detect language
        original_lang = detect(user_input)
        if original_lang == "fr":
            translated_input = GoogleTranslator(source='fr', target='en').translate(user_input)
        else:
            translated_input = user_input

        # Load credentials
        openai_api_key = os.getenv("OPENAI_API_KEY")
        airtable_key = os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        table_name = os.getenv("AIRTABLE_TABLE_NAME")

        # Load data from Airtable
        df = fetch_airtable_data(airtable_key, base_id, table_name)
        loader = DataFrameLoader(df, page_content_column="text")
        docs = loader.load()
        vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings(openai_api_key=openai_api_key))

        # Custom prompt
        prompt_template = PromptTemplate(
            template="""
You are a professional luxury concierge agent.

Your job is to recommend the best restaurant(s) from a list of options based on a client’s request.

👉 If you find a match that is NOT in the exact location requested (e.g. arrondissement, neighborhood, or city), you MUST clearly and politely say this:
- Example: “This restaurant is located just outside the requested area but offers all the desired features.”

Be profesionnal, concise, and personalized.

Client Request:
{context}
""",
            input_variables=["context"]
        )

        # AI chain
        llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": prompt_template}
        )

        result = qa_chain.run(translated_input)

        # Translate back if needed
        if original_lang == "fr":
            result = GoogleTranslator(source='en', target='fr').translate(result)

        # Display result
        st.subheader("📝 Suggested AI Response:")
        st.success(result)

        # Generate and download PDF
        pdf_path = generate_proposal_pdf("Client (EBA/ESMA)", user_input, result, 70)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Télécharger la proposition (PDF)" if original_lang == "fr" else "📄 Download Proposal (PDF)", f, file_name="proposal.pdf")
