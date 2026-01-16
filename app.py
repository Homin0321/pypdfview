import os
import tempfile

import pymupdf.layout  # activate PyMuPDF-Layout in pymupdf
import pymupdf4llm
import streamlit as st
from dotenv import load_dotenv
from google import genai
from streamlit_pdf_viewer import pdf_viewer

# Set page configuration - this should be the first Streamlit command
st.set_page_config(
    page_title="PDF to Markdown Converter",
    page_icon="📄",
    layout="wide",
)


@st.dialog(title="Page Summary", width="large")
def summary_dialog(text):
    st.markdown(text)


@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY is not set. Please check your .env file.")
        return None
    return genai.Client(api_key=api_key)


def summarize_page(text):
    client = get_gemini_client()
    if not client:
        return None

    prompt = "Analyze the following text and provide a piece of organized summary: "
    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest", contents=prompt + text
        )
        return response.text
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None


def initialize_state():
    """Initializes session state variables if they don't exist."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "pages" not in st.session_state:
        st.session_state.pages = []
    if "total_pages" not in st.session_state:
        st.session_state.total_pages = 0
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    if "md_text" not in st.session_state:
        st.session_state.md_text = ""


def reset_state():
    """Resets the state when a new file is uploaded or file is removed."""
    st.session_state.current_page = 0
    st.session_state.pages = []
    st.session_state.total_pages = 0
    st.session_state.uploaded_file_name = None
    st.session_state.md_text = ""


def main():
    """
    Main function to run the Streamlit app.
    """
    load_dotenv()
    initialize_state()

    st.sidebar.title("📄 PDF to Markdown")

    # --- Sidebar for interactions ---
    uploaded_file = st.sidebar.file_uploader(
        "Choose a PDF file", type="pdf", help="Upload a PDF to convert it to Markdown"
    )

    if uploaded_file is not None:
        # If a new file is uploaded, reset the state
        if st.session_state.uploaded_file_name != uploaded_file.name:
            reset_state()
            st.session_state.uploaded_file_name = uploaded_file.name

        # Process the file only if the pages haven't been generated yet
        if not st.session_state.pages:
            temp_pdf_path = None
            with st.spinner(f"Converting `{uploaded_file.name}` to Markdown..."):
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as temp_pdf:
                        temp_pdf.write(uploaded_file.getvalue())
                        temp_pdf_path = temp_pdf.name

                    # Use page_chunks=True to get a list of page data dictionaries
                    page_data_list = pymupdf4llm.to_markdown(
                        temp_pdf_path,
                        page_chunks=True,  # This activates the page-chunking feature
                    )
                    st.session_state.pages = page_data_list
                    st.session_state.total_pages = len(page_data_list)

                    # Combine all page texts for the full markdown content
                    full_md_text = "".join([page["text"] for page in page_data_list])
                    st.session_state.md_text = full_md_text

                except Exception as e:
                    st.sidebar.error(f"An error occurred: {e}")
                finally:
                    if temp_pdf_path and os.path.exists(temp_pdf_path):
                        os.remove(temp_pdf_path)

        # --- Display content and navigation if pages are available ---
        if st.session_state.pages:
            total_pages = st.session_state.total_pages
            current_page_index = st.session_state.current_page

            # --- Navigation controls in the sidebar ---
            # Page jump input
            def handle_page_jump():
                page_jump = st.session_state.page_jump_input
                if 1 <= page_jump <= total_pages:
                    st.session_state.current_page = page_jump - 1
                else:
                    st.sidebar.warning(
                        f"Page number must be between 1 and {total_pages}."
                    )

            st.sidebar.number_input(
                f"Go to page (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=current_page_index + 1,
                step=1,
                on_change=handle_page_jump,
                key="page_jump_input",
            )

            # Ensure current_page_index is within valid bounds
            if current_page_index < 0:
                st.session_state.current_page = 0
                current_page_index = 0
            elif current_page_index >= total_pages:
                st.session_state.current_page = total_pages - 1
                current_page_index = total_pages - 1

            # --- Layout controls in the sidebar ---
            ratio_options = ["2:0", "1.5:0.5", "1:1", "0.5:1.5", "0:2"]
            selected_ratio = st.sidebar.select_slider(
                "Width Ratio (PDF : Markdown)", options=ratio_options, value="1:1"
            )

            if st.sidebar.button("Summarize Page", width="stretch"):
                with st.spinner("Summarizing..."):
                    summary = summarize_page(
                        st.session_state.pages[current_page_index]["text"]
                    )
                    if summary:
                        summary_dialog(summary)

            # --- Side-by-Side Display ---
            pdf_container = None
            md_container = None

            if selected_ratio == "2:0":
                pdf_container = st.container()
            elif selected_ratio == "0:2":
                md_container = st.container()
            else:
                parts = selected_ratio.split(":")
                r1 = float(parts[0])
                r2 = float(parts[1])
                pdf_container, md_container = st.columns([r1, r2])

            if pdf_container:
                with pdf_container:
                    # st.subheader("Original PDF")
                    pdf_viewer(
                        uploaded_file.getvalue(),
                        pages_to_render=[current_page_index + 1],
                        zoom_level="auto",
                    )

            if md_container:
                with md_container:
                    # st.subheader("Markdown Output")
                    st.markdown(
                        st.session_state.pages[current_page_index]["text"],
                        unsafe_allow_html=True,
                    )

            # --- Download button in the sidebar ---
            st.sidebar.download_button(
                label="📥 Download .md file",
                data=st.session_state.md_text.encode("utf-8"),
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}.md",
                mime="text/markdown",
            )
    else:
        # If no file is uploaded, ensure the state is clean
        if st.session_state.uploaded_file_name is not None:
            reset_state()
        st.info("Please upload a PDF file using the sidebar to get started.")


if __name__ == "__main__":
    main()
