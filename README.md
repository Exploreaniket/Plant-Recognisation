# 🌱 PlantID — Smart Plant Recognition & Care Web App  
**AI-powered plant identification + care tips + user profiles**

PlantID is a Flask-based AI web application that allows users to:
- Upload plant images
- Automatically identify plants using **Google Gemini AI**
- Get detailed care instructions
- Track their identification history
- Manage their profile & avatar
- Reset profile stats anytime

This project is built for beginners while including powerful real-world features.

---

## 🚀 Features

### 🔍 Plant Identification
- Upload an image from your system
- Gemini AI detects:
  - Plant name
  - Common name
  - Confidence rate
  - Care tips (light, water, soil, notes)

### 🧠 Powered by Google Gemini API
- Uses `gemini-1.5-flash`
- Forced JSON responses for safe processing
- Fully server-side logic

### 👤 User Accounts
- Register / Login / Logout
- Encrypted passwords (Werkzeug)
- SQLite database
- Persistent user sessions

### 🖼 Profile Management
- Click avatar to change profile picture
- Edit name & bio
- Reset profile button:
  - Deletes plant history
  - Resets plant count
  - Keeps account intact

### 🧾 Identification History
- Main page shows last identification
- Profile page shows recent plant cards

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Bootstrap 5, Vanilla JS |
| Backend | Flask (Python) |
| AI | Google Gemini API |
| Database | SQLite (via SQLAlchemy) |
| Image Handling | Pillow |
| Auth | Secure password hashing (Werkzeug) |
| Storage | Local `uploads/` folder |




---

## 🔑 Environment Setup

### 1️⃣ Create a virtual environment

```bash
python -m venv venv

ACTIVATE

venv\Scripts\activate     =for win


source venv/bin/activate    =mac/linux

DEPENDENCY

pip install -r requirements.txt


CREATE .env FILE
GEMINI_API_KEY=YOUR_KEY_HERE





## 👨‍💻 Author

**Developed by:**  
 **Aniket Prajapati** 
📧 Email:prajapatianiket020@gmail.com 
🔗 GitHub:Exploreaniket


