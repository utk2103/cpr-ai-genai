import streamlit as st
import os
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates import *
from io import BytesIO
from fpdf import FPDF

# Robust API key handling
def get_api_key():
    try:
        # Attempt to retrieve the API key from Streamlit secrets
        api_key = st.secrets["key"]
        if not api_key:
            st.error("API key is empty. Please check your Streamlit secrets configuration.")
            return None
        return api_key
    except KeyError:
        st.error("API key not found in Streamlit secrets. Please configure the key.")
        return None

# Initialize OpenAI with error handling
def initialize_llm():
    try:
        # Retrieve the API key
        api_key = get_api_key()
        
        # Check if API key is valid
        if not api_key:
            st.error("Unable to retrieve a valid API key.")
            return None
        
        # Initialize OpenAI with the retrieved key
        llm = OpenAI(
            openai_api_key=api_key, 
            temperature=0.75,
            # Add additional parameters for more robust initialization
            max_tokens=1000,
            model="gpt-3.5-turbo-instruct"  # Specify the model explicitly
        )
        return llm
    
    except Exception as e:
        st.error(f"Error initializing OpenAI: {str(e)}")
        return None

# Function to generate content
def generate_content(template, sector, topic):
    # Initialize LLM with comprehensive error checking
    llm = initialize_llm()
    
    # Validate LLM initialization
    if llm is None:
        st.error("Failed to initialize OpenAI. Please check your API key and try again.")
        return None
    
    try:
        # Create and run the prompt chain
        prompt = PromptTemplate(
            input_variables=["sector", "topic"], 
            template=template
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Generate content with error handling
        generated_content = chain.run(sector=sector, topic=topic)
        
        # Additional validation of generated content
        if not generated_content or generated_content.strip() == "":
            st.error("Content generation failed. The response was empty.")
            return None
        
        return generated_content
    
    except Exception as e:
        st.error(f"Error during content generation: {str(e)}")
        return None

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
        # Validate inputs
        if not sector or not topic:
            st.error("❌ Please enter both sector and topic!")
            return

        # Attempt content generation
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

            # Handle generated content
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
                st.error("Content generation failed. Please check your inputs and API key.")

    # Reset Button
    if st.button("Reset Fields"):
        st.session_state.clear()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
