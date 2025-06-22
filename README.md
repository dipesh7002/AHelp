# 🌐 AHelp

AHelp is a modular Django web application enhanced with Tailwind CSS, designed to deliver a responsive, user-friendly support platform. It follows a clean architecture separating concerns across client interfaces, core logic, and user management.

---

## 🛠 Tech Stack

- **Backend:** Django (Python)  
- **Frontend:** Tailwind CSS  
- **Database:** SQLite (Development)  
- **Deployment:** Vercel (via `vercels.json`)  
- **Package Management:** npm  

---

## 📁 Project Structure

```
AHelp/
├── client/            # Client-facing views and templates
├── core/              # Core site-wide logic and configuration
├── helper/            # Utility modules and helper functions
├── home/              # Static pages (e.g., Home, About Us)
├── user/              # User authentication and profiles
├── theme/             # Tailwind CSS theme and layout configs
├── media/uploads/     # Uploaded media files
├── static/images/     # Static image assets
├── db.sqlite3         # SQLite database (for development)
├── manage.py          # Django management script
├── package.json       # Node.js project config
├── tailwind.config.js # Tailwind CSS configuration
├── vercels.json       # Vercel deployment configuration
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/dipesh7002/AHelp.git
cd AHelp
```

### 2. Set Up Python Environment

```bash
python -m venv env
source env/bin/activate       # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
npm install
```

### 4. Run Development Server

```bash
python manage.py migrate
python manage.py runserver
```

### 5. Watch Tailwind CSS

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch
```

---

## ✨ Features

- 🔹 Clean, modular Django app architecture  
- 🔹 Tailwind CSS integration for modern UI  
- 🔹 Responsive Home and About Us pages  
- 🔹 User authentication system  
- 🔹 Media and static file handling  
- 🔹 Ready for Vercel deployment  

---

## 📌 Recent Updates

- ✅ Updated About Us & Home pages  
- ✅ Improved static image handling  
- ✅ Fixed redirection issues  
