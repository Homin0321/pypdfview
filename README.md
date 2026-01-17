# AI PDF Viewer

This project is a Streamlit application that converts PDF files into Markdown format. It leverages the `pymupdf4llm` library to perform the conversion and `streamlit-pdf-viewer` to display PDF pages side-by-side with their AI-enhanced Markdown counterparts.

## Features

*   **PDF Upload:** Upload PDF files directly through the Streamlit interface.
*   **Side-by-Side View:** View the original PDF page alongside its converted Markdown content.
*   **Adjustable Layout:** Use a slider to adjust the width ratio between the PDF viewer and the Markdown output.
*   **Page Navigation:** Easily navigate through the pages of the PDF or jump to a specific page.
*   **Table of Contents:** Access and navigate the PDF's internal Table of Contents.
*   **Summary Generation:** Generate a concise, organized summary of any page using Google Gemini.
*   **Chat with Page:** Ask questions about specific pages or a range of pages using an integrated AI chat interface.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd pypdfview
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Google Gemini API Key:**
    To use the AI features (summarization and chat), you need a Google Gemini API key.
    *   Create a `.env` file in the root directory and add:
        ```env
        GEMINI_API_KEY=your_api_key_here
        ```

## Usage

1.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

2.  Open your web browser and navigate to the URL provided (usually `http://localhost:8501`).

3.  Use the sidebar to upload a PDF file. The application will automatically process the pages and display them.

## Dependencies

*   `streamlit`
*   `pymupdf`
*   `pymupdf4llm`
*   `streamlit-pdf-viewer`
*   `google-genai`
*   `python-dotenv`
