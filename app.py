import openai
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure OpenAI API Key
openai.api_key = "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"

# Database setup
DATABASE = "faq_system.db"

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faq_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_to_db(user_query, response):
    """Log the query and response to the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO faq_logs (user_query, response) VALUES (?, ?)', (user_query, response))
    conn.commit()
    conn.close()

def get_chatgpt_response(user_query):
    """Get response from ChatGPT."""
    prompt = f"You are a support assistant. Answer the following question in one paragraph: {user_query}"
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/ask', methods=['POST'])
def ask():
    """Handle user queries."""
    data = request.get_json()
    user_query = data.get("question", "")
    
    if not user_query:
        return jsonify({"error": "Question is required"}), 400

    # Get ChatGPT response
    response = get_chatgpt_response(user_query)

    # Log to database
    log_to_db(user_query, response)

    return jsonify({"response": response})

@app.route('/logs', methods=['GET'])
def logs():
    """Retrieve query logs."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, response, timestamp FROM faq_logs')
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"logs": [{"query": row[0], "response": row[1], "timestamp": row[2]} for row in rows]})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
