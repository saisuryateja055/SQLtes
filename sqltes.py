import streamlit as st
import sqlite3
import pandas as pd
from streamlit_ace import st_ace  # For SQL syntax highlighting
import sqlparse  # For formatting SQL queries

# Initialize session state for query history
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Function to get database schema
def get_schema(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema[table_name] = [(col[1], col[2]) for col in columns]  # (name, type)
    return schema

# Function to display table data
def display_table(table_name, conn):
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            st.markdown(f"**Data in '{table_name}' Table:**")
            st.dataframe(df, use_container_width=True)
        else:
            st.markdown(f"Table '{table_name}' is empty.")
    except sqlite3.Error as e:
        st.error(f"Error displaying table: {e}")

# Function to display schema
def display_schema(conn):
    schema = get_schema(conn)
    if schema:
        st.markdown("**Database Schema:**")
        for table, columns in schema.items():
            st.markdown(f"**Table: {table}**")
            df = pd.DataFrame(columns, columns=["Column Name", "Data Type"])
            st.dataframe(df, use_container_width=True)
    else:
        st.markdown("No tables in the database.")

# Streamlit app layout
st.set_page_config(layout="wide", page_title="SQLtes", page_icon=":books:")

# Custom CSS for UI
st.markdown("""
    <style>
    /* Main container styling */
    .stApp {
        background: linear-gradient(205deg, #0d9488 0%, #2563eb 50%, #4f46e5 100%);
        color: #e0e0e0;
        font-family: 'Open Sans', sans-serif;
    }
    /* Remove top padding/margin */
    .block-container {
        padding-top: 0.5rem !important;
        margin-top: 0 !important;
    }
    /* Title styling (h1) */
    h1 {
        color: #ff6f61;
        font-size: 3em;
        margin: 0;
        padding: 10px 0;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
    }
    /* Header styling (h2, h3) */
    h2, h3 {
        color: #a3e635;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
    }
    /* Dataframe styling */
    .stDataFrame {
        background: #ffffff;
        border-radius: 8px;
        padding: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    /* Button styling */
    .stButton>button {
        background-color: #f4d03f;
        color: #0d9488;
        border-radius: 6px;
        font-weight: 600;
        padding: 8px 16px;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #d4ac0d;
    }
    /* Selectbox styling */
    .stSelectbox select {
        background-color: #ffffff;
        color: #0d9488;
        border-radius: 6px;
        padding: 5px;
    }
    /* Code block styling */
    .stCodeBlock {
        background-color: #1e1e1e;
        border-radius: 6px;
        padding: 8px;
    }
    /* Expander styling */
    .stExpander {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* Text area (ACE editor) */
    .ace_editor {
        border-radius: 6px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    /* Remove unnecessary margins */
    .stMarkdown, .stText {
        margin-bottom: 0.5rem;
    }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&family=Roboto:wght@400;500&family=Open+Sans:wght@400;500&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Database name input on main page
st.header("Database Selection")
db_name = st.text_input("Enter Database Name", value="my_database")
if st.button("Load/Create Database"):
    if db_name.strip():
        # Sanitize database name to prevent invalid characters
        db_name = ''.join(c for c in db_name if c.isalnum() or c in ['_', '-'])
        st.session_state.db_file = f"{db_name}.sqlite"
        # Reconnect to the new database
        conn = sqlite3.connect(st.session_state.db_file, check_same_thread=False)
        cursor = conn.cursor()
        # Create sample table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                city TEXT
            )
        ''')
        conn.commit()
        st.success(f"Connected to database: {db_name}.sqlite")
    else:
        st.error("Please enter a valid database name.")

# Initialize database connection (use default if not set)
if 'db_file' not in st.session_state:
    st.session_state.db_file = "default.sqlite"
conn = sqlite3.connect(st.session_state.db_file, check_same_thread=False)
cursor = conn.cursor()

# Single, centered, large title
st.markdown("<h1>SQLtes</h1>", unsafe_allow_html=True)
st.markdown("<h2>Execute SQL commands and watch your database evolve in real time!</h2>", unsafe_allow_html=True)

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["SQL Editor", "Schema View", "Query History"])

# Tab 1: SQL Editor
with tab1:
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        st.header("SQL Command Input")
        st.markdown("Enter any valid SQL command (e.g., CREATE, INSERT, UPDATE, DELETE, SELECT, DROP).")

        # Example queries in an expander
        with st.expander("Explore Example Queries", expanded=False):
            tutorial_level = st.selectbox("Select Tutorial Level", ["Beginner", "Intermediate", "Advanced"])
            example_queries = {
                "Beginner": [
                    "INSERT INTO users (name, age, city) VALUES ('Alice', 25, 'New York')",
                    "SELECT * FROM users WHERE age > 20",
                    "UPDATE users SET age = 30 WHERE name = 'Alice'"
                ],
                "Intermediate": [
                    "CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, grade INTEGER)",
                    "SELECT name, city FROM users ORDER BY age DESC",
                    "DELETE FROM users WHERE age < 18"
                ],
                "Advanced": [
                    "CREATE TABLE orders (order_id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, FOREIGN KEY(user_id) REFERENCES users(id))",
                    "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id",
                    "DROP TABLE IF EXISTS students"
                ]
            }
            selected_query = st.selectbox("Try an Example Query", example_queries[tutorial_level])
            if st.button("Load Example Query"):
                st.session_state.sql_command = selected_query

        # SQL editor with syntax highlighting
        sql_command = st_ace(
            value=st.session_state.get('sql_command', 'SELECT * FROM users'),
            language="sql",
            theme="monokai",
            height=200,
            auto_update=True
        )

        if st.button("Execute SQL"):
            try:
                formatted_sql = sqlparse.format(sql_command, reindent=True)
                st.session_state.query_history.append(formatted_sql)

                if sql_command.strip().upper().startswith("SELECT"):
                    df = pd.read_sql_query(sql_command, conn)
                    if not df.empty:
                        st.markdown("**Query Results:**")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.markdown("No results returned.")
                else:
                    cursor.executescript(sql_command)
                    conn.commit()
                    st.success("Command executed successfully!")
            except sqlite3.Error as e:
                st.error(f"Error: {e}. Try checking your SQL syntax or table names.")

    with col2:
        st.header("Table View (Real-Time)")
        schema = get_schema(conn)
        if schema:
            selected_table = st.selectbox("Select Table to Display", list(schema.keys()))
            display_table(selected_table, conn)
        else:
            st.markdown("No tables to display.")

# Tab 2: Schema View
with tab2:
    st.header("Database Schema")
    display_schema(conn)

# Tab 3: Query History
with tab3:
    st.header("Query History")
    if st.session_state.query_history:
        for i, query in enumerate(st.session_state.query_history):
            st.code(query, language="sql")
    else:
        st.markdown("No queries executed yet.")

# Footer
st.markdown("**Note**: Use the tabs to explore the database schema, query history, or execute SQL commands. Check example queries in the SQL Editor tab!")
