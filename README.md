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
