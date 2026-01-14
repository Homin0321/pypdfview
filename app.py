import os
import tempfile

import fitz
import pymupdf.layout  # activate PyMuPDF-Layout in pymupdf
import pymupdf4llm
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

# Set page configuration - this should be the first Streamlit command
st.set_page_config(
    page_title="PDF to Markdown Converter",
    page_icon="📄",
    layout="wide",
)


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

                    st.sidebar.success("✅ Conversion successful!")
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
            st.sidebar.divider()
            st.sidebar.write(f"Page {current_page_index + 1} of {total_pages}")

            col1, col2 = st.sidebar.columns(2)

            def prev_page():
                st.session_state.current_page -= 1

            def next_page():
                st.session_state.current_page += 1

            # Previous button logic
            col1.button(
                "⬅️ Prev",
                width="stretch",
                disabled=(current_page_index <= 0),
                on_click=prev_page,
            )

            # Next button logic
            col2.button(
                "Next ➡️",
                width="stretch",
                disabled=(current_page_index >= total_pages - 1),
                on_click=next_page,
            )

            # Ensure current_page_index is within valid bounds
            if current_page_index < 0:
                st.session_state.current_page = 0
                current_page_index = 0
            elif current_page_index >= total_pages:
                st.session_state.current_page = total_pages - 1
                current_page_index = total_pages - 1

            # --- Side-by-Side Display ---
            col_pdf, col_md = st.columns(2)

            with col_pdf:
                # st.subheader("Original PDF")
                pdf_viewer(
                    uploaded_file.getvalue(),
                    pages_to_render=[current_page_index + 1],
                    zoom_level="auto",
                )

            with col_md:
                # st.subheader("Markdown Output")
                st.markdown(
                    st.session_state.pages[current_page_index]["text"],
                    unsafe_allow_html=True,
                )

            # --- Download button in the sidebar ---
            st.sidebar.divider()
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
