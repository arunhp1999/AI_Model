
# GPT SQL Assistant (Streamlit + OpenAI)

This is a natural language SQL assistant built with Streamlit, OpenAI GPT, and MySQL.
Ask questions like "Show me tasks per project" and get real SQL queries with results and interactive charts.

## 🔧 Local Setup

### 1. Prepare your environment

- Rename `.env_template` → `.env`
- Paste your **OpenAI API key** inside `.env` like this:

```
OPENAI_API_KEY=your-openai-api-key-here
```

> ⚠️ **NEVER commit your real key** to GitHub. Keep `.env` in `.gitignore`.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

## 🚀 Deploying to Streamlit Cloud

1. Push your project to GitHub
2. Go to https://share.streamlit.io
3. Connect your GitHub repo and set secrets:

```
OPENAI_API_KEY = your-real-openai-api-key
```

## 📁 Folder Structure

```
gpt_sql_chat_app/
├── app.py
├── .env_template
├── requirements.txt
├── bi_knowledge_base.txt
├── README.md
└── modules/
    ├── documents_schema.csv
    ├── projects_schema.csv
    └── tasks_schema.csv
```
