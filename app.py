import os
import re

import pymupdf
import pymupdf.layout  # activate PyMuPDF-Layout in pymupdf
import pymupdf4llm
import streamlit as st
from dotenv import load_dotenv
from google import genai
from streamlit_pdf_viewer import pdf_viewer

# Set page configuration - this should be the first Streamlit command
st.set_page_config(
    page_title="AI PDF Viewer",
    page_icon="📄",
    layout="wide",
)


def fix_bold_symbol_issue(md: str) -> str:
    pattern = re.compile(r"\*\*(.+?)\*\*(\s*)", re.DOTALL)

    def repl(m):
        inner = m.group(1)
        after = m.group(2)
        # Add space after ** if content contains symbols and no space exists
        if re.search(r"[^0-9A-Za-z\s]", inner) and after == "":
            return f"**{inner}** "
        return m.group(0)

    return pattern.sub(repl, md)


@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY is not set. Please check your .env file.")
        return None
    return genai.Client(api_key=api_key)


@st.dialog(title="Page Summary", width="large")
def summary_dialog(text):
    st.markdown(text)


def ensure_pages_loaded(pdf_stream, page_indices):
    indices_to_load = [idx for idx in page_indices if idx not in st.session_state.pages]

    if indices_to_load:
        with st.spinner(
            f"Loading pages {min(indices_to_load) + 1}-{max(indices_to_load) + 1}..."
        ):
            try:
                doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
                indices_to_load.sort()
                page_data_list = pymupdf4llm.to_markdown(
                    doc,
                    pages=indices_to_load,
                    header=False,
                    footer=False,
                    page_chunks=True,
                )
                for i, page_data in enumerate(page_data_list):
                    real_idx = indices_to_load[i]
                    st.session_state.pages[real_idx] = page_data
                doc.close()
            except Exception as e:
                st.error(f"Error loading pages: {e}")
                for idx in indices_to_load:
                    if idx not in st.session_state.pages:
                        st.session_state.pages[idx] = {"text": "Error loading page."}


@st.dialog(title="Chat with Page", width="large")
def chat_dialog(current_page_index, total_pages, pdf_stream):
    col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="bottom")
    with col1:
        start_page = st.number_input(
            "Start Page",
            min_value=1,
            max_value=total_pages,
            value=current_page_index + 1,
            step=1,
            key="chat_start_page",
        )
    with col2:
        end_page = st.number_input(
            "End Page",
            min_value=1,
            max_value=total_pages,
            value=current_page_index + 1,
            step=1,
            key="chat_end_page",
        )
    with col3:
        clear_clicked = st.button("Clear Chat History", width="stretch")

    if start_page is None or end_page is None:
        return

    start_page = int(start_page)
    end_page = int(end_page)

    if start_page > end_page:
        st.error("Start page must be less than or equal to end page.")
        return

    selected_indices = list(range(start_page - 1, end_page))
    ensure_pages_loaded(pdf_stream, selected_indices)

    context_text = ""
    for idx in selected_indices:
        page_text = st.session_state.pages.get(idx, {}).get("text", "")
        context_text += f"{page_text}\n\n"

    # Use integer key for single page to maintain backward compatibility
    if len(selected_indices) == 1:
        chat_key = selected_indices[0]
    else:
        chat_key = f"{selected_indices[0]}-{selected_indices[-1]}"

    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}

    if chat_key not in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_key] = []

    if clear_clicked:
        st.session_state.chat_histories[chat_key] = []
        st.rerun()

    for message in st.session_state.chat_histories[chat_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask something about these pages..."):
        st.session_state.chat_histories[chat_key].append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            client = get_gemini_client()
            if client:
                history_context = ""
                for msg in st.session_state.chat_histories[chat_key][:-1]:
                    history_context += f"{msg['role']}: {msg['content']}\n"

                full_prompt = f"Context:\n{context_text}\n\nChat History:\n{history_context}\nUser: {prompt}\nAnswer:"

                with st.spinner("Thinking..."):
                    try:
                        response = client.models.generate_content(
                            model="gemini-flash-lite-latest", contents=full_prompt
                        )
                        fixed_text = fix_bold_symbol_issue(response.text)
                        st.markdown(fixed_text)
                        st.session_state.chat_histories[chat_key].append(
                            {"role": "assistant", "content": fixed_text}
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")


@st.dialog(title="Table of Contents")
def toc_dialog():
    toc = st.session_state.get("toc", [])
    if not toc:
        st.markdown("No Table of Contents found.")
    else:
        for i, item in enumerate(toc):
            lvl, title, page = item[0], item[1], item[2]
            prefix = "—" * (lvl - 1)
            label = f"{prefix} {title} (p. {page})"
            if st.button(label, key=f"toc_btn_{i}", use_container_width=True):
                st.session_state.current_page = page - 1
                st.rerun()


def summarize_page(text):
    client = get_gemini_client()
    if not client:
        return None

    prompt = "Analyze the following text and provide a piece of organized summary: "
    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest", contents=prompt + text
        )
        return fix_bold_symbol_issue(response.text)
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None


def initialize_state():
    """Initializes session state variables if they don't exist."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "pages" not in st.session_state or not isinstance(st.session_state.pages, dict):
        st.session_state.pages = {}
    if "total_pages" not in st.session_state:
        st.session_state.total_pages = 0
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    if "toc" not in st.session_state:
        st.session_state.toc = []
    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}


def reset_state():
    """Resets the state when a new file is uploaded or file is removed."""
    st.session_state.current_page = 0
    st.session_state.pages = {}
    st.session_state.total_pages = 0
    st.session_state.uploaded_file_name = None
    st.session_state.toc = []
    st.session_state.chat_histories = {}


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

            # Open document to get basic info
            try:
                doc = pymupdf.open(stream=uploaded_file.getvalue(), filetype="pdf")
                st.session_state.toc = doc.get_toc()
                st.session_state.total_pages = doc.page_count
                doc.close()
            except Exception as e:
                st.error(f"Error opening PDF: {e}")
                reset_state()
                return

        # Ensure we have total_pages
        total_pages = st.session_state.total_pages
        if total_pages == 0:
            st.warning("The PDF seems to be empty or invalid.")
            return

        # Ensure current_page_index is within valid bounds
        current_page_index = st.session_state.current_page
        if current_page_index < 0:
            st.session_state.current_page = 0
            current_page_index = 0
        elif current_page_index >= total_pages:
            st.session_state.current_page = total_pages - 1
            current_page_index = total_pages - 1

        # Ensure current page is loaded
        ensure_pages_loaded(uploaded_file.getvalue(), [current_page_index])

        # --- Navigation controls in the sidebar ---
        # Page jump input
        def handle_page_jump():
            page_jump = st.session_state.page_jump_input
            if 1 <= page_jump <= total_pages:
                st.session_state.current_page = page_jump - 1
            else:
                st.sidebar.warning(f"Page number must be between 1 and {total_pages}.")

        st.sidebar.number_input(
            f"Go to page (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=current_page_index + 1,
            step=1,
            on_change=handle_page_jump,
            key="page_jump_input",
        )

        # --- Layout controls in the sidebar ---
        ratio_options = ["2:0", "1.5:0.5", "1:1", "0.5:1.5", "0:2"]
        selected_ratio = st.sidebar.select_slider(
            "Width Ratio (PDF : Markdown)", options=ratio_options, value="1:1"
        )

        if st.sidebar.button("Table of Contents", width="stretch"):
            toc_dialog()

        current_page_text = st.session_state.pages[current_page_index]["text"]

        if st.sidebar.button("Summarize All", width="stretch"):
            with st.spinner("Summarizing..."):
                all_indices = list(range(total_pages))
                ensure_pages_loaded(uploaded_file.getvalue(), all_indices)

                full_text = ""
                for idx in all_indices:
                    page_text = st.session_state.pages.get(idx, {}).get("text", "")
                    full_text += f"{page_text}\n\n"

                summary = summarize_page(full_text)
                if summary:
                    summary_dialog(summary)

        if st.sidebar.button("Summarize This Page", width="stretch"):
            with st.spinner("Summarizing..."):
                summary = summarize_page(current_page_text)
                if summary:
                    summary_dialog(summary)

        if st.sidebar.button("Chat with Gemini", width="stretch"):
            chat_dialog(current_page_index, total_pages, uploaded_file.getvalue())

        # Check if all pages are loaded
        all_pages_loaded = len(st.session_state.pages) == total_pages

        if all_pages_loaded:
            full_text = ""
            for idx in range(total_pages):
                page_text = st.session_state.pages.get(idx, {}).get("text", "")
                full_text += f"{page_text}\n\n"

            st.sidebar.download_button(
                label="Download Markdown",
                data=full_text,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            if st.sidebar.button("Download Markdown", width="stretch"):
                with st.spinner("Loading all pages..."):
                    all_indices = list(range(total_pages))
                    ensure_pages_loaded(uploaded_file.getvalue(), all_indices)
                st.rerun()

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
                    current_page_text,
                    unsafe_allow_html=True,
                )

    else:
        # If no file is uploaded, ensure the state is clean
        if st.session_state.uploaded_file_name is not None:
            reset_state()
        st.info("Please upload a PDF file using the sidebar to get started.")


if __name__ == "__main__":
    main()
