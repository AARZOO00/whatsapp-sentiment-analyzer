# WhatsApp Sentiment Analyzer (v2.0 - Production Grade)

This is a powerful, production-grade WhatsApp chat sentiment analyzer with advanced NLP capabilities, a professional dashboard UI, and a scalable architecture. It is designed for deep insights into chat conversations, suitable for enterprise demonstration and portfolio use.

## Features

### Core NLP Intelligence
-   **Multilingual Support:** Automatically detects the language of each message and can be extended to translate non-English text for analysis.
-   **Hybrid Sentiment Analysis:** Combines VADER (rule-based) and a Transformer model (HuggingFace) to provide a robust ensemble sentiment score with confidence.
-   **Emotion Detection:** Identifies emotions such as joy, sadness, anger, fear, surprise, and neutrality within messages.
-   **Toxicity & Safety Analysis:** Detects abusive language, hate speech, and profanity, generating a toxicity score and risk indicator for the chat.
-   **AI Chat Summarization:** Provides an automatic summary of the conversation, highlighting key topics and emotional trends.

### Backend (FastAPI)
-   **Modular Architecture:** NLP logic is separated into `services/nlp_service.py` for clean code and maintainability.
-   **Asynchronous Processing:** Utilizes FastAPI's `BackgroundTasks` for heavy ML computations, ensuring a responsive API.
-   **Robust WhatsApp Chat Parser:** Supports various Android and iPhone export formats, handles multiline messages, media omitted lines, and multilingual text. Returns detailed debug information for parsing failures.
-   **Structured API Responses:** Uses Pydantic schemas for clear, validated data exchange.
-   **Auto Cleanup:** Uploaded files are processed in-memory and not stored persistently, eliminating the need for explicit file cleanup.
-   **Logging & Error Handling:** Comprehensive logging and robust error handling to prevent crashes and provide meaningful feedback.
-   **Model Caching:** Uses `functools.lru_cache` to cache loaded NLP models, improving performance.
-   **Environment Configuration:** Uses `config.py` for managing settings and environment variables.

### Frontend (React + TypeScript)
-   **Professional Analytics Dashboard:** A modern, card-based UI with an intuitive layout for data visualization.
-   **KPI Cards:** Displays key performance indicators for Total Messages, Overall Sentiment (Ensemble), Toxicity Risk, and Total Toxic Messages.
-   **Interactive Charts:**
    -   Bar chart for most active users.
    -   Pie chart for emotion distribution.
    -   Pie chart for language distribution.
-   **AI Summary Display:** Presents the generated chat summary prominently.
-   **Dark / Light Mode Toggle:** Allows users to switch between themes for personalized viewing.
-   **Loading Animations & Smooth Transitions:** Enhances user experience during data processing.
-   **Mobile Responsive Design:** Ensures a seamless experience across various devices.
-   **Export Functionality:** Export chat analysis data to CSV format. PDF export is a placeholder.
-   **Filter Functionality:** Placeholder UI for filtering data by date and participant is present.

### Engineering Quality
-   **Clean Folder Structure:** Well-organized project directory for easy navigation and understanding.
-   **No Broken Imports or Missing Files:** All dependencies and internal modules are correctly referenced.
-   **Type-Safe Frontend Code:** Developed with TypeScript to ensure code reliability and reduce runtime errors.
-   **API Validation and Schemas:** Pydantic models used for strict request and response validation in the backend.
-   **Caching for Repeated Analysis:** `lru_cache` used for NLP models to optimize performance.
-   **Environment Configuration:** Utilizes `config.py` for managing application settings.
-   **Docker Support:** Dockerfile provided for easy containerization and deployment.

---

## Project Structure

```
whatsapp-sentiment-analyzer/
 ├── backend/
 │   ├── main.py                     # FastAPI application entry point
 │   ├── config.py                   # Environment and application settings
 │   ├── schemas.py                  # Pydantic models for API data validation
 │   ├── requirements.txt            # Python dependencies
 │   └── services/
 │       └── nlp_service.py          # All core NLP logic (parsing, sentiment, emotion, etc.)
 ├── frontend/
 │   ├── src/
 │   │   ├── main.tsx                # Frontend entry point
 │   │   ├── App.tsx                 # Main React component, handles routing and data flow
 │   │   ├── index.css               # Global styles and theme definitions
 │   │   └── components/             # Reusable React components (charts, cards, upload)
 │   │       ├── FileUpload.tsx
 │   │       ├── Dashboard.tsx
 │   │       ├── StatCard.tsx
 │   │       ├── UserChart.tsx
 │   │       ├── EmotionChart.tsx
 │   │       ├── LanguageDistributionChart.tsx
 │   │       └── EmojiList.tsx
 │   ├── package.json                # Frontend dependencies
 ├── Dockerfile                      # Dockerfile for containerization
 ├── .env.example                    # Example environment variables
 └── README.md                       # Project documentation (this file)
 └── sample_chat.txt                 # Sample WhatsApp chat file for testing
```

---

## Installation and Run Instructions

To get the application up and running, follow these steps:

### 1. Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd whatsapp-sentiment-analyzer/backend
    ```

2.  **Create a Python Virtual Environment (recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    *   **On Windows:**
        ```powershell
        .\venv\Scripts\activate
        ```
    *   **On macOS / Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The first time you run the backend, it will download several large NLP models (Transformer, Emotion, Toxicity, Summarization). This might take a few minutes depending on your internet connection. Subsequent runs will use cached models.*

5.  **Run the FastAPI Server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend API will be available at `http://127.0.0.1:8000`. Keep this terminal open.

### 2. Frontend Setup

1.  **Navigate to the frontend directory (in a new terminal):**
    ```bash
    cd whatsapp-sentiment-analyzer/frontend
    ```

2.  **Install Node.js Dependencies:**
    ```bash
    npm install
    ```

3.  **Start the React Development Server:**
    ```bash
    npm run dev
    ```
    The frontend application will open in your browser, usually at `http://localhost:5173`.

### 3. Docker Deployment (Backend)

To deploy the backend using Docker:

1.  **Navigate to the project root directory:**
    ```bash
    cd whatsapp-sentiment-analyzer/
    ```

2.  **Build the Docker image:**
    ```bash
    docker build -t whatsapp-sentiment-analyzer-backend .
    ```

3.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 whatsapp-sentiment-analyzer-backend
    ```
    The backend will be accessible at `http://localhost:8000`.

---

## Testing

Use the provided `sample_chat.txt` file (located in the root of the `whatsapp-sentiment-analyzer` directory) to test the application. This file contains various chat formats and types of messages to demonstrate the parser's robustness.

---

## Architecture Explanation

### Backend
The backend is built with FastAPI, designed for high performance and easy API development.
-   **`main.py`:** Serves as the main entry point for the FastAPI application. It defines API routes (`/analyze`, `/results/{job_id}`, `/ping`), handles file uploads, and manages asynchronous job processing using `BackgroundTasks`. It uses an in-memory `job_store` for job status tracking.
-   **`services/nlp_service.py`:** Contains all the core NLP business logic. This includes:
    -   A robust `parse_whatsapp_chat` function to handle diverse WhatsApp export formats.
    -   Integration with multiple HuggingFace Transformer models for sentiment, emotion, toxicity, and summarization.
    -   VADER for rule-based sentiment analysis.
    -   `langdetect` for language identification.
    -   Aggregation logic to combine results and calculate overall metrics (e.g., ensemble sentiment, language distribution).
    -   `functools.lru_cache` is used to efficiently load and cache NLP models, preventing redundant downloads and speeding up subsequent analyses.
-   **`schemas.py`:** Defines Pydantic models for API request and response validation, ensuring data integrity and providing automatic OpenAPI documentation.
-   **`config.py`:** Manages application settings and loads environment variables, facilitating easy configuration management.

### Frontend
The frontend is a modern, single-page application built with React and TypeScript, designed for an intuitive user experience.
-   **`App.tsx`:** The main application component. It orchestrates the data flow, manages global state (loading, errors, analysis results), and handles the asynchronous communication with the backend, including polling for analysis results. It also implements the dark/light mode toggle.
-   **`components/`:** This directory houses reusable UI components:
    -   **`FileUpload.tsx`:** Handles file selection and drag-and-drop, initiating the analysis process.
    -   **`Dashboard.tsx`:** The central component for displaying all analysis results, organizing them into KPI cards, charts, and summary sections.
    -   **`StatCard.tsx`:** A generic component for displaying key metrics.
    -   **`UserChart.tsx`, `EmotionChart.tsx`, `LanguageDistributionChart.tsx`:** Specialized Recharts components for interactive data visualization.
    -   **`EmojiList.tsx`:** Displays the most frequently used emojis.
-   **`api.ts`:** Centralizes all API calls to the FastAPI backend, providing a clean interface for frontend components.
-   **`index.css`:** Contains global styles and theme-related CSS variables to support the dark/light mode functionality.

---

This comprehensive setup provides a powerful and user-friendly WhatsApp sentiment analysis tool, ready for advanced use cases.