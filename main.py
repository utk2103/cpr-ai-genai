import streamlit as st
import os
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates import *
from io import BytesIO
from fpdf import FPDF

# More flexible API key handling
def get_api_key():
    # Try to get API key from Streamlit secrets
    try:
        return st.secrets["key"]
    except KeyError:
        pass
    
    # Try to get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # If no API key found, show input field
    if 'OPENAI_API_KEY' not in st.session_state:
        st.session_state.OPENAI_API_KEY = ''
    
    api_key = st.sidebar.text_input("Enter your OpenAI API key:", 
                                   value=st.session_state.OPENAI_API_KEY,
                                   type="password")
    if api_key:
        st.session_state.OPENAI_API_KEY = api_key
        return api_key
    return None

# Initialize OpenAI with API key handling
def initialize_llm():
    api_key = get_api_key()
    if api_key:
        try:
            llm = OpenAI(openai_api_key=api_key, temperature=0.75)
            return llm
        except Exception as e:
            st.error(f"Error initializing OpenAI: {str(e)}")
            return None
    return None

# Function to generate content
def generate_content(template, sector, topic):
    llm = initialize_llm()
    if llm is None:
        st.error("Please provide a valid OpenAI API key to generate content.")
        return None
    
    prompt = PromptTemplate(input_variables=["sector", "topic"], template=template)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(sector=sector, topic=topic)

# Function to convert text to a PDF
def convert_to_pdf(content):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer, dest='S').encode('latin1')
    pdf_buffer.seek(0)
    
    return pdf_buffer

# Streamlit App
def main():
    st.set_page_config(page_title="CPR-AI Content Generator", layout="centered")
    st.title("CPR-AI Content Generation Tool ⚒️")

    # Sidebar for content type selection
    if "content_type" not in st.session_state:
        st.session_state.content_type = "Press Release"

    content_type = st.sidebar.selectbox(
        "Select Content Type",
        ["Press Release", "Guest Column", "Leadership Article", "Blog Post", "Social Media"],
        index=["Press Release", "Guest Column", "Leadership Article", "Blog Post", "Social Media"].index(st.session_state.content_type)
    )

    # Input fields with session state persistence
    sector = st.text_input("Enter Industry Sector:", value=st.session_state.get("sector", ""))
    topic = st.text_input("Enter Topic:", value=st.session_state.get("topic", ""))

    # Generate content button
    if st.button("Generate Content"):
        if sector and topic:
            with st.spinner("Generating content..."):
                template_map = {
                    "Press Release": PRESS_RELEASE_TEMPLATE,
                    "Guest Column": GUEST_COLUMN_TEMPLATE,
                    "Leadership Article": LEADERSHIP_ARTICLE_TEMPLATE,
                    "Blog Post": BLOG_POST_TEMPLATE,
                    "Social Media": SOCIAL_MEDIA_TEMPLATE
                }
                
                template = template_map[content_type]
                generated_content = generate_content(template, sector, topic)

                if generated_content:
                    # Store generated content in session state
                    st.session_state.generated_content = generated_content

                    # Display generated content
                    st.subheader("Generated Content:")
                    st.markdown(generated_content)

                    # Convert content to PDF for download
                    pdf_buffer = convert_to_pdf(generated_content)
                    st.download_button(
                        label="Download as PDF",
                        data=pdf_buffer,
                        file_name=f"{content_type.lower().replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
        else:
            st.error("❌ Please enter both sector and topic!")

    # Reset Button
    if st.button("Reset Fields"):
        # Keep API key when resetting
        api_key = st.session_state.get('OPENAI_API_KEY', '')
        st.session_state.clear()
        st.session_state.OPENAI_API_KEY = api_key
        st.experimental_rerun()

if __name__ == "__main__":
    main()
