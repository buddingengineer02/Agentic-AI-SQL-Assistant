# Agentic AI SQL Assistant

A lightweight, local, multi-agent AI SQL Assistant designed to convert natural language queries into safe SQLite statements, audit them using security compliance guidelines, and present them for execution. It is fully optimized for low-RAM machines.

---

## Setup Instructions

Follow these 5 simple steps to get the app running:

1. **Download the project** into your workspace directory.
2. **Install the required packages** in stages using the commands below:
   ```bash
   py -3.11 -m pip install streamlit sqlalchemy sqlparse pandas python-dotenv
   py -3.11 -m pip install langchain langchain-google-genai
   py -3.11 -m pip install crewai
   ```
3. **Get a free Gemini API key** from [Google AI Studio](https://aistudio.google.com).
4. **Configure your environment**: Open the `.env` file and replace `your_gemini_api_key_here` with your actual Google Gemini API key:
   ```env
   GOOGLE_API_KEY=AIzaSy...
   ```
5. **Run the Streamlit application**:
   ```bash
   py -3.11 -m streamlit run app.py
   ```

---

## How to Use Your Own Database

You can upload and run queries against any database of your choice:
1. Open the application in your browser.
2. Drag and drop any `.sqlite` or `.db` file into the file uploader located at the top of the sidebar.
3. The app will immediately switch to the new database, update the sidebar schema explorer, and generate 3 custom sample questions based on the new schema without making any external API calls.
