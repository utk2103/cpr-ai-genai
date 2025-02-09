import streamlit as st
import os
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates import *  # Ensure templates.py exists
from io import BytesIO
from fpdf import FPDF

# ✅ FIXED: Ensure API Key is imported correctly
try:
    OPENAI_API_KEY = st.secrets["key"]
    st.write("✅ API key successfully loaded!")
except KeyError:
    st.error("❌ ERROR: `OPENAI_API_KEY` not found in Streamlit secrets.")
    OPENAI_API_KEY = None  # Ensure it doesn't cause a NameError later

# ✅ FIXED: Correct `OpenAI` initialization\
if OPENAI_API_KEY:
    llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.75)
else:
    st.error("❌ OpenAI API key is missing. Check your `.streamlit/secrets.toml` or Streamlit Cloud secrets.")

# Function to generate content
def generate_content(template, sector, topic):
    prompt = PromptTemplate(input_variables=["sector", "topic"], template=template)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(sector=sector, topic=topic)

# Function to convert text to a PDF and return as a BytesIO object
def convert_to_pdf(content):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)

    # Save PDF to memory instead of file system
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer, dest='S').encode('latin1')  # Corrected encoding issue
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
        st.session_state.clear()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
