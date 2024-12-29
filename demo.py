import openai
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API Key securely
openai.api_key = os.getenv( "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")

# Initialize SQLite database
DB_FILE = "faq_logs.db"
def init_db():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")

init_db()

# Define a root route
@app.route('/')
def home():
    return "Welcome to the Automated FAQ System! Use the /ask endpoint to interact with the system."

# Define the /ask route
@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Parse JSON request
        data = request.get_json(silent=True)
        if not data or "question" not in data:
            return jsonify({"error": "Invalid request. A 'question' field is required."}), 400

        user_question = data["question"]

        # Call OpenAI API to generate a response
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Use the latest model
                messages=[
                    {"role": "system", "content": "You are a support assistant."},
                    {"role": "user", "content": user_question}
                ],
                max_tokens=150
            )
            ai_response = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return jsonify({"error": f"Failed to generate response: {str(e)}"}), 500

        # Log the question and response to the database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO logs (question, response, timestamp) VALUES (?, ?, ?)",
                (user_question, ai_response, timestamp)
            )
            conn.commit()

        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Define the /logs route with pagination
@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, question, response, timestamp FROM logs LIMIT ? OFFSET ?",
                (per_page, offset)
            )
            rows = cursor.fetchall()

        logs = [
            {"id": row[0], "question": row[1], "response": row[2], "timestamp": row[3]}
            for row in rows
        ]
        return jsonify(logs)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "False") == "True")
