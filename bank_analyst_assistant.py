import sqlite3
import random
import pandas as pd
from datetime import datetime, date
from faker import Faker
import ollama
import streamlit as st
import os

# Initialize Faker for mock data
fake = Faker('uz_UZ')  # Uzbek locale for names/regions

DB_PATH = 'bank.db'

# Custom SQLite date adapter
def adapt_date(val):
    return val.isoformat()

# Register the adapter
sqlite3.register_adapter(date, adapt_date)

def init_database():
    """Generate mock database with at least 1M transactions if not exists."""
    if os.path.exists(DB_PATH):
        print("Database already exists. Skipping generation.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            birth_date DATE,
            region TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            balance REAL,
            open_date DATE,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            amount REAL,
            date DATE,
            type TEXT,  -- 'debit' or 'credit'
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    ''')

    # Mock data generation
    regions = ['Toshkent viloyati', 
               'Samarqand viloyati',
                'Buxoro viloyati', 
                'Farg\'ona viloyati', 
                'Andijon viloyati', 
                'Namangan viloyati', 
                'Qashqadaryo viloyati', 
                'Surxondaryo viloyati', 
                'Jizzax viloyati', 
                'Xorazm viloyati',
                'Navoiy viloyati',
                'Sirdaryo viloyati',
                'Qoraqalpog\'iston Respublikasi',
                'Toshkent shahri']
    
    # Generate 100,000 clients
    clients = []
    for _ in range(100000):
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
        region = random.choice(regions)
        clients.append((fake.name(), birth_date, region))
    
    c.executemany("INSERT INTO clients (name, birth_date, region) VALUES (?, ?, ?)", clients)
    conn.commit()
    
    client_ids = [i[0] for i in c.execute("SELECT id FROM clients").fetchall()]
    
    # Generate 200,000 accounts
    accounts = []
    for _ in range(200000):
        client_id = random.choice(client_ids)
        balance = round(random.uniform(0, 1000000), 2)  # Up to 1M balance
        open_date = fake.date_between(start_date='-5y', end_date='today')
        accounts.append((client_id, balance, open_date))
    
    c.executemany("INSERT INTO accounts (client_id, balance, open_date) VALUES (?, ?, ?)", accounts)
    conn.commit()
    
    account_ids = [i[0] for i in c.execute("SELECT id FROM accounts").fetchall()]
    
    # Generate 1,000,000 transactions
    transactions = []
    types = ['debit', 'credit']
    for _ in range(1000000):
        account_id = random.choice(account_ids)
        amount = round(random.uniform(-5000, 5000), 2)  # Negative for debit
        date = fake.date_between(start_date='-1y', end_date='today')
        trans_type = 'debit' if amount < 0 else 'credit'
        amount = abs(amount) if trans_type == 'debit' else amount
        transactions.append((account_id, amount, date, trans_type))
    
    c.executemany("INSERT INTO transactions (account_id, amount, date, type) VALUES (?, ?, ?, ?)", transactions)
    conn.commit()
    
    conn.close()
    print("Mock database generated with 100K clients, 200K accounts, 1M transactions.")


def get_schema():
    # Placeholder: Replace with your actual schema retrieval logic
    return """
    Tables:
    - transactions (id, account_id, amount, date, type)
    - accounts (id, client_id)
    - clients (id, name, region)
    """



def generate_sql(query: str) -> str:
    """Use local LLM to generate SQL from natural language query."""
    schema = get_schema()

    a = "Translate the following Uzbek natural language query to a valid SQLite SQL query. "

    prompt = f"""
    You are a SQL expert for a bank database using SQLite. Schema:
    {schema}
    
    Translate the following text query to a valid SQLite SQL query. 
    Rules:
    - Use SQLite-compatible functions (e.g., strftime('%Y-%m', date) for year/month, strftime('%m', date) for month, not EXTRACT).
    - Use lowercase table names: transactions, accounts, clients.
    - Use table aliases: t for transactions, a for accounts, c for clients.
    - Use exact region values (e.g., 'Toshkent viloyati', 'Samarqand viloyati').
    - Available regions: 'Toshkent viloyati', 'Samarqand viloyati', 'Buxoro viloyati', 'Farg\'ona viloyati', 'Andijon viloyati', 'Namangan viloyati', 'Qashqadaryo viloyati', 'Surxondaryo viloyati', 'Jizzax viloyati', 'Xorazm viloyati', 'Navoiy viloyati', 'Sirdaryo viloyati', 'Qoraqalpog\'iston Respublikasi', 'Toshkent shahri'.
    - Do not include markdown (```sql or similar), leading/trailing spaces, explanations or texts like this "Here is the translated query:".
    - Return only the SQL query, nothing else.
    Examples:
    1. Query: "2024 yil iyun oyida Toshkent viloyati bo‘yicha jami tranzaksiyalar summasini ko‘rsat"
       SQL: SELECT SUM(t.amount) AS total_transactions FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y-%m', t.date) = '2024-06' AND c.region = 'Toshkent viloyati';
    2. Query: "2023 yil may oyida Samarqand viloyati bo‘yicha kredit tranzaksiyalar sonini ko‘rsat"
       SQL: SELECT COUNT(*) AS credit_count FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y-%m', t.date) = '2023-05' AND c.region = 'Samarqand viloyati' AND t.type = 'credit';
    3. Query: "Buxoro viloyati bo‘yicha 2024 yilda eng ko‘p tranzaksiya qilgan mijozni ko‘rsat"
       SQL: SELECT c.name, COUNT(*) AS transaction_count FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y', t.date) = '2024' AND c.region = 'Buxoro viloyati' GROUP BY c.id, c.name ORDER BY transaction_count DESC LIMIT 1;
    4. Query: "2024 yil Toshkent viloyati bo‘yicha har bir oy uchun tranzaksiyalar summasini ko‘rsat"
       SQL: SELECT strftime('%m', t.date) AS month, SUM(t.amount) AS total_transactions FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y', t.date) = '2024' AND c.region = 'Toshkent viloyati' GROUP BY strftime('%m', t.date) ORDER BY month;
    5. Query: "2024 yilning birinchi choragida Toshkent viloyati bo‘yicha o‘rtacha tranzaksiya summasini ko‘rsat"
       SQL: SELECT AVG(t.amount) AS avg_transaction FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y', t.date) = '2024' AND strftime('%m', t.date) IN ('01', '02', '03') AND c.region = 'Toshkent viloyati';
    6. Query: "2024 yil Andijon viloyati bo‘yicha debet tranzaksiyalarining umumiy summasini ko‘rsat"
       SQL: SELECT SUM(t.amount) AS total_debit FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y', t.date) = '2024' AND c.region = 'Andijon viloyati' AND t.type = 'debit';
    7. Query: "2024 yilning iyun oyida har bir viloyat bo‘yicha tranzaksiyalar sonini ko‘rsat"
       SQL: SELECT c.region, COUNT(*) AS transaction_count FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y-%m', t.date) = '2024-06' GROUP BY c.region ORDER BY c.region;    
    8. Query: "2023 yilda Toshkent viloyati bo‘yicha eng katta tranzaksiya qilgan mijozni ko‘rsat"
       SQL: SELECT c.name, MAX(t.amount) AS max_transaction FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y', t.date) = '2023' AND c.region = 'Toshkent viloyati' GROUP BY c.id, c.name ORDER BY max_transaction DESC LIMIT 1;   
       Query: {query}
    """
    try:
        response = ollama.generate(model='llama3', prompt=prompt)
        sql = response['response'].strip()
        if not sql:
            raise ValueError("Generated SQL is empty")
        # Debug: Log raw and parsed SQL
        print(f"Raw Ollama response: {response['response']}")
        print(f"Parsed SQL: {sql}")
        return sql
    except Exception as e:
        st.error(f"Failed to generate SQL: {str(e)}. Please ensure Ollama is running and the 'llama3' model is available.")
        return ""
    

def execute_query(sql: str) -> pd.DataFrame:
    """Execute SQL and return DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


def export_to_excel(df: str, filename: str, chart_type: str = 'bar'):
    """Export DataFrame to Excel with a chart."""
    if df.empty:
        return
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Results', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Results']
        
        chart = None
        if chart_type == 'bar' and len(df.columns) >= 2:
            chart = workbook.add_chart({'type': 'bar'})
            # Assume first column is category, second is value
            chart.add_series({
                'categories': ['Results', 1, 0, len(df), 0],
                'values': ['Results', 1, 1, len(df), 1],
            })
            chart.set_title({'name': 'Bar Chart'})
        elif chart_type == 'pie' and len(df) <= 10:  # Pie for small data
            chart = workbook.add_chart({'type': 'pie'})
            chart.add_series({
                'categories': ['Results', 1, 0, len(df), 0],
                'values': ['Results', 1, 1, len(df), 1],
            })
            chart.set_title({'name': 'Pie Chart'})
        
        if chart:
            worksheet.insert_chart('F2', chart)


def run_ui():
    st.title("Bank Data Analyst Assistant")
    st.write("Enter your natural language query in Uzbek (e.g., '2024 yil iyun oyida Toshkent viloyati bo‘yicha jami tranzaksiyalar summasini ko‘rsat')")
    
    user_query = st.text_input("Query:")
    
    if st.button("Generate Report"):
        if user_query:
            with st.spinner("Generating SQL..."):
                sql = generate_sql(user_query)
                if not sql:
                    st.error("No SQL query generated. Please check Ollama setup.")
                    return
                st.write("Generated SQL:")
                st.code(sql, language='sql')
            
            with st.spinner("Executing query..."):
                try:
                    df = execute_query(sql)
                    st.write("Results:")
                    st.dataframe(df)
                    
                    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    with st.spinner("Exporting to Excel..."):
                        export_to_excel(df, filename, 'bar')
                    
                    with open(filename, 'rb') as f:
                        st.download_button("Download Excel Report", f.read(), file_name=filename)
                except Exception as e:
                    pass
                    # st.error(f"Query execution failed: {str(e)}. Please check the SQL query for SQLite compatibility.")
        else:
            st.warning("Please enter a query.")

if __name__ == "__main__":
    init_database()  # Run once
    run_ui()  # Start Streamlit
