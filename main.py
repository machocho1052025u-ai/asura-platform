import os
import sqlite3
import secrets
import hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))
DB_FILE = "asura_users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_api_key(api_key: str) -> bool:
    if not api_key:
        return False
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE api_key = ?", (api_key,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Web UI Layout (Gemini / ChatGPT Style)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASURA AI PLATFORM</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background: #0b0b10; color: #e0e0e0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background: #12121c; border-right: 1px solid #1f1f2e; display: flex; flex-direction: column; padding: 15px; }
        .logo { font-size: 20px; font-weight: bold; color: #00ffcc; text-align: center; margin-bottom: 25px; }
        .nav-btn { background: #1a1a26; color: #aaa; border: 1px solid #2a2a3d; padding: 12px; border-radius: 8px; margin-bottom: 10px; cursor: pointer; text-align: left; }
        .nav-btn.active { background: #00ffcc; color: #000; font-weight: bold; }
        .main-panel { flex: 1; display: flex; flex-direction: column; background: #0f0f15; padding: 20px; }
        .chat-container { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 15px; }
        .chat-bubble { max-width: 80%; padding: 12px 16px; border-radius: 12px; font-size: 14px; white-space: pre-wrap; }
        .chat-bubble.user { background: #1f1f30; align-self: flex-end; color: #fff; }
        .chat-bubble.ai { background: #161622; align-self: flex-start; border: 1px solid #252538; color: #00ffcc; }
        .chat-input-box { display: flex; gap: 10px; padding: 15px; background: #12121c; }
        .chat-input-box input { flex: 1; background: #1a1a26; border: 1px solid #2a2a3d; padding: 14px; border-radius: 8px; color: #fff; outline: none; }
        .chat-input-box button { background: #00ffcc; color: #000; font-weight: bold; border: none; padding: 0 20px; border-radius: 8px; cursor: pointer; }
        .auth-box { max-width: 400px; margin: auto; background: #161622; padding: 30px; border-radius: 12px; border: 1px solid #00ffcc; text-align: center; }
        .auth-box input { width: 100%; padding: 12px; margin: 10px 0; background: #0b0b10; border: 1px solid #2a2a3d; border-radius: 6px; color: #fff; }
        .auth-box button { width: 100%; padding: 12px; background: #00ffcc; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">⚡ ASURA PLATFORM</div>
        {% if user %}
            <button class="nav-btn active">💬 Gemini / AI Studio</button>
            <div style="margin-top:auto; background:#181824; padding:10px; border-radius:8px; font-size:12px;">
                User: <span style="color:#00ffcc;">{{ user }}</span><br><br>
                API Key:<br><code style="color:#00ffcc; font-size:10px;">{{ api_key }}</code><br><br>
                <a href="/logout" style="color:#ff6666;">Logout</a>
            </div>
        {% endif %}
    </div>
    <div class="main-panel">
        {% if user %}
            <div class="chat-container" id="chatLogs">
                <div class="chat-bubble ai">မင်္ဂလာပါ {{ user }}! ASURA AI Platform မှ ကြိုဆိုပါတယ်။ ဘာကူညီပေးရမလဲ?</div>
            </div>
            <div class="chat-input-box">
                <input type="text" id="userPrompt" placeholder="Ask Asura AI..." onkeypress="if(event.key==='Enter') sendPrompt()">
                <button onclick="sendPrompt()">Send</button>
            </div>
        {% else %}
            <div class="auth-box">
                <h2 style="color:#00ffcc; margin-bottom: 15px;">ASURA PLATFORM</h2>
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
                <hr style="border-color:#252538; margin: 15px 0;">
                <form action="/register" method="post">
                    <input type="text" name="username" placeholder="New Username" required>
                    <input type="password" name="password" placeholder="New Password" required>
                    <button type="submit" style="background:#00b386; color:#fff;">Register Account</button>
                </form>
            </div>
        {% endif %}
    </div>
    <script>
        function sendPrompt() {
            let input = document.getElementById('userPrompt');
            let val = input.value.trim();
            if(!val) return;

            let chatLogs = document.getElementById('chatLogs');
            let uBubble = document.createElement('div');
            uBubble.className = 'chat-bubble user';
            uBubble.innerText = val;
            chatLogs.appendChild(uBubble);
            input.value = '';

            fetch('/api/v1/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer {{ api_key }}'
                },
                body: JSON.stringify({ prompt: val })
            })
            .then(res => res.json())
            .then(data => {
                let aiBubble = document.createElement('div');
                aiBubble.className = 'chat-bubble ai';
                aiBubble.innerText = data.result || "Processed.";
                chatLogs.appendChild(aiBubble);
                chatLogs.scrollTop = chatLogs.scrollHeight;
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    if "username" in session:
        return render_template_string(HTML_TEMPLATE, user=session["username"], api_key=session["api_key"])
    return render_template_string(HTML_TEMPLATE, user=None)

@app.route("/api/v1/generate", methods=["POST"])
def api_generate():
    auth_header = request.headers.get("Authorization", "")
    api_key = auth_header.replace("Bearer ", "").strip()
    if not verify_api_key(api_key):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    return jsonify({"status": "success", "result": f"Asura AI Processed: {prompt}"})

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    api_key = "asura_" + secrets.token_hex(16)
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, api_key) VALUES (?, ?, ?)",
                       (username, hash_password(password), api_key))
        conn.commit()
        conn.close()
        session["username"] = username
        session["api_key"] = api_key
        return redirect(url_for("index"))
    except Exception:
        return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key FROM users WHERE username = ? AND password_hash = ?", 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    if user:
        session["username"] = username
        session["api_key"] = user[0]
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
  
