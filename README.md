# AI Desktop Assistant

A modular Python desktop application integrating local LLM and TTS capabilities, built with PySide6.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Model Setup:**
    -   Place your GGUF Llama model file in `models/llama/`.
    -   Update `src/core/config.py` if your model filename differs or you want to change default paths.
    -   Place any TTS models in `models/tts/` if required by your chosen TTS backend.

3.  **Run the Application:**
    ```bash
    python src/main.py
    ```

## Structure
-   `src/`: Source code using a clean layout.
-   `models/`: Directory for large binary model files (ignored by git).
-   `data/`: Directory for local database `app_database.db`.
