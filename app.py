import os
import streamlit as st
import pandas as pd
import mysql.connector
from openai import OpenAI
import plotly.express as px

# --- Load environment variables ---
from dotenv import load_dotenv
load_dotenv()

# --- GPT client setup ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Streamlit page config ---
st.set_page_config(page_title="AI SQL Assistant", layout="wide")
st.title("🧠 AI SQL Assistant for MySQL + BI")

# --- Load BI knowledge ---
@st.cache_data
def load_bi_knowledge(path="bi_knowledge_base.txt"):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

bi_knowledge = load_bi_knowledge()

# --- Load schema modules ---
@st.cache_data
def load_schema(module):
    df = pd.read_csv(f"modules/{module}_schema.csv")
    return df.to_string(index=False)

# --- DB connection ---
@st.cache_resource
def connect_to_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

# --- Chat memory ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Detect relevant modules using GPT ---
def detect_modules(user_input):
    module_prompt = f"""
You are a smart assistant. Given the user question below, return only relevant module names (Documents, Projects, Tasks) as a list.

User question: "{user_input}"
Relevant modules:
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": module_prompt}]
    )
    modules = response.choices[0].message.content.strip().replace("'", "").replace('"', "").split(",")
    return [m.strip("[]").strip().lower() for m in modules if m.strip()]

# --- Build prompt for SQL generation ---
def build_prompt(user_input, modules):
    schema_descriptions = "\n\n".join([load_schema(m) for m in modules])
    formatted_chat_history = "\n".join(
        [f"User: {x['question']}\nSQL: {x['sql']}\nResult: {x['df_head']}" for x in st.session_state.chat_history[-3:]]
    )
    return f"""
You are a MySQL assistant with BI context.

Schema:
{schema_descriptions}

BI Insights:
{bi_knowledge}

Conversation so far:
{formatted_chat_history}

User: {user_input}
SQL:
"""

# --- Run SQL and visualize ---
def run_query(query):
    conn = connect_to_db()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- UI: input ---
user_input = st.text_input("Ask a data question:")

if user_input:
    try:
        # Step 1: Detect modules
        modules = detect_modules(user_input)
        st.write("📦 Using Modules:", modules)

        # Step 2: Build prompt
        prompt = build_prompt(user_input, modules)

        # Step 3: Get SQL from GPT
        sql_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        query = sql_response.choices[0].message.content.strip()
        st.code(query, language="sql")

        # Step 4: Run query
        df = run_query(query)
        st.dataframe(df)

        # Step 5: Add to history
        st.session_state.chat_history.append({
            "question": user_input,
            "sql": query,
            "df_head": df.head(3).to_dict()
        })

        # Step 6: Chart (if numeric + group)
        if len(df.columns) >= 2:
            x, y = df.columns[0], df.columns[1]
            if pd.api.types.is_numeric_dtype(df[y]):
                fig = px.bar(df, x=x, y=y)
                st.plotly_chart(fig, use_container_width=True)

        # Step 7: Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇ Download CSV", csv, "result.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error: {e}")
