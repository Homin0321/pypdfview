# PDF to Markdown Converter

This project is a Streamlit application that converts PDF files into Markdown format. It leverages the `pymupdf4llm` library to perform the conversion and `streamlit-pdf-viewer` to display PDF pages.

## Features

*   **PDF Upload:** Upload PDF files directly through the Streamlit interface.
*   **Side-by-Side View:** View the original PDF page alongside its converted Markdown content.
*   **Page Navigation:** Easily navigate through the pages of the PDF.
*   **Markdown Download:** Download the complete converted Markdown content as a `.md` file.
*   **Temporary File Handling:** Efficiently handles temporary files during the conversion process.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd pypdf
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You may need to create a `requirements.txt` file containing the dependencies listed below.)*

4.  **Set up Google Gemini API Key:**
    To use the summarization feature, you need a Google Gemini API key. You can either:
    *   Set it as an environment variable: `export GOOGLE_API_KEY="your_api_key"`
    *   Enter it directly in the application sidebar.

## Usage

1.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

2.  Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

3.  Use the sidebar to upload a PDF file. The application will automatically convert it to Markdown and display the content. You can then navigate through pages and download the `.md` file.

4.  If you haven't set the Gemini API key as an environment variable, enter it in the sidebar. Then, click "Summarize Page" to get a summary of the current page.

## Dependencies

*   `streamlit`
*   `pymupdf`
*   `pymupdf4llm`
*   `streamlit-pdf-viewer`
*   `google-genai`
