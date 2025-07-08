import os
import streamlit as st
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import mysql.connector
import plotly.express as px

# Load environment variables
load_dotenv()
client = OpenAI()  # Initialize OpenAI client using API key from .env

# Load BI knowledge base
@st.cache_data
def load_bi_knowledge(path="bi_knowledge_base.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

bi_knowledge = load_bi_knowledge()

# Load schema for all modules
@st.cache_data
def load_schemas():
    schemas = {}
    modules_path = "modules"
    for filename in os.listdir(modules_path):
        if filename.endswith(".csv"):
            module_name = filename.replace("_schema.csv", "")
            df = pd.read_csv(os.path.join(modules_path, filename))
            schemas[module_name] = df
    return schemas

schemas = load_schemas()

# Detect relevant modules using GPT
def detect_modules(user_input):
    module_prompt = f"""
You are an AI that selects relevant modules for a SQL query.
Modules available: {list(schemas.keys())}
User question: {user_input}
List only relevant modules (comma-separated).
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": module_prompt}]
    )
    modules = response.choices[0].message.content.strip()
    return [m.strip().lower() for m in modules.split(",")]

# Format schema to feed into prompt
def format_schema(modules):
    desc = ""
    for m in modules:
        if m in schemas:
            desc += f"\nModule: {m}\n"
            desc += schemas[m].to_string(index=False)
            desc += "\n"
    return desc

# Generate SQL from GPT
def generate_sql(user_input, schema_desc, chat_memory, bi_knowledge):
    prompt = f"""
You are a MySQL assistant with BI context.

Schema:
{schema_desc}

BI Insights:
{bi_knowledge}

Conversation so far:
{chat_memory}

User: {user_input}
SQL:
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Connect to MySQL
@st.cache_resource
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Arunahp@1999",
        database="web_center_db"
    )

db_conn = connect_to_db()

# Session chat memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# UI Setup
st.set_page_config(page_title="AI SQL Assistant", layout="wide")
st.title("🤖 GPT-Powered SQL Assistant with BI Knowledge")

user_input = st.text_input("Ask a question about your data:")

if user_input:
    with st.spinner("🔎 Understanding your question..."):
        # Step 1: detect modules
        modules = detect_modules(user_input)

        # Step 2: format schema
        schema_desc = format_schema(modules)

        # Step 3: format chat memory
        chat_memory = ""
        for item in st.session_state.chat_history[-3:]:
            chat_memory += f"\nUser: {item['question']}\nSQL: {item['sql']}\nPreview: {item['df_head']}\n"

        # Step 4: generate SQL
        query = generate_sql(user_input, schema_desc, chat_memory, bi_knowledge)

        # ✅ Cleanup GPT code fences if present
        if query.startswith("```"):
            query = query.strip("```").strip()
            if query.lower().startswith("sql"):
                query = query[3:].strip()

        # Step 5: execute query
        try:
            df = pd.read_sql(query, db_conn)
            st.success("✅ Query executed successfully!")
            st.code(query, language="sql")
            st.dataframe(df)

            # Step 6: store history
            st.session_state.chat_history.append({
                "question": user_input,
                "sql": query,
                "df_head": df.head(3).to_dict()
            })

            # Step 7: chart
            if len(df.columns) >= 2:
                x_col, y_col = df.columns[:2]
                fig = px.bar(df, x=x_col, y=y_col)
                st.plotly_chart(fig)
                st.download_button("📥 Export CSV", df.to_csv(index=False), "result.csv", "text/csv")

        except Exception as e:
            st.error(f"❌ Error executing SQL:\n\n{e}")
