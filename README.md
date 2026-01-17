# PDF to Markdown Converter

This project is a Streamlit application that converts PDF files into Markdown format. It leverages the `pymupdf4llm` library to perform the conversion and `streamlit-pdf-viewer` to display PDF pages.

## Features

*   **PDF Upload:** Upload PDF files directly through the Streamlit interface.
*   **Side-by-Side View:** View the original PDF page alongside its converted Markdown content.
*   **Page Navigation:** Easily navigate through the pages of the PDF.
*   **Summary Generation:** Generate a concise summary of the PDF content using Google Gemini.

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
    *   Create a `.env` file in the root directory and add the line: `GOOGLE_API_KEY=your_api_key`

## Usage

1.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

2.  Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

3.  Use the sidebar to upload a PDF file. The application will automatically convert it to Markdown and display the content.

## Dependencies

*   `streamlit`
*   `pymupdf`
*   `pymupdf4llm`
*   `streamlit-pdf-viewer`
*   `google-genai`
