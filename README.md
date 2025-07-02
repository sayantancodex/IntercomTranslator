
# 🗣️ Multilingual Chat App (English ↔ Bengali)

A real-time web-based chat application that supports **automatic translation** between **English** and  **Bengali** , with support for **Benglish (Romanized Bengali)** input. Designed for seamless bilingual communication between two users.

---

## ✨ Features

* 🔄 Real-time chat with WebSockets (Socket.IO)
* 🌐 Automatic translation (English ↔ Bengali)
* 🔡 Benglish transliteration using `indic-transliteration`
* 👁️ Toggle between translated and original message text
* 💬 WhatsApp-style UI with Tailwind CSS
* 👥 2-user limit per room with session management
* 📂 Optional JSON mapping for custom translations

---

## 🛠️ Tech Stack

* **Backend** : Flask + Flask-SocketIO + Eventlet
* **Frontend** : HTML + Tailwind CSS + Socket.IO
* **Translation** : deep-translator (Google Translate)
* **Transliteration** : indic-transliteration

---

## 📆 Project Structure

```
multilingual-chat/
├── app.py                    # Flask server with Socket.IO
├── translation_mappings.json # Optional mappings for fixed translations
├── templates/
│   └── index.html            # Chat UI
├── static/                   # (Optional) Static assets
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/sayantancodex/IntercomTranslator
cd IntercomTranslator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python app.py
```

Open your browser at:

📍 `http://localhost:5000`

---

## 💬 Usage

1. Enter your name and select your preferred language (English or Bengali).
2. Chat starts when 2 users are connected.
3. Messages are translated for the recipient based on their language.
4. A **"Show Original / Show Translated"** button lets users toggle views per message.

---

## 🔌 Dependencies

* [Flask](https://flask.palletsprojects.com/)
* [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
* [eventlet](https://eventlet.net/)
* [deep-translator](https://pypi.org/project/deep-translator/)
* [indic-transliteration](https://pypi.org/project/indic-transliteration/)
* [Tailwind CSS](https://tailwindcss.com/) (via CDN)

---

## 🧰 Future Improvements

* ✅ Add support for more Indian languages
* 📆 Add chat history persistence (DB or JSON)
* ☕ Dockerize for production deployment
* ☁️ Deploy on Render / Railway / Fly.io
