# 🎓 Face Recognition Attendance System

A web-based **Face Recognition Attendance System** built with **Python (Flask)** and **OpenCV**, featuring an intuitive and modern UI powered by **Tailwind CSS**.
This project allows admins to manage users, record attendance using face recognition, and view attendance reports in real-time.

---

## 🚀 Features

* 🔐 **Secure Admin Login System**

  * Only registered admins can access the dashboard.
  * Add new admins securely with password hashing.

* 👨‍🎓 **User Management**

  * Register students/users with Roll Number, Name, and Image.
  * Automatically train the recognition model after adding users.

* 📸 **Face Recognition Attendance**

  * Detect and recognize faces in real-time using a webcam.
  * Automatically mark attendance when a face is recognized.

* 📊 **Attendance Dashboard**

  * View daily attendance reports.
  * Filter and search attendance records by date.

* 💧 **Modern UI**

  * Fully responsive interface styled with **Tailwind CSS**.
  * Semi-transparent panels and watermark branding.

* 🖋️ **Watermark Branding**

  * A subtle “@made by Sonal and Manpreet” watermark at the bottom.

---

## 🧰 Technologies Used

| Component            | Technology         |
| -------------------- | ------------------ |
| **Frontend**         | HTML, Tailwind CSS |
| **Backend**          | Flask (Python)     |
| **Database**         | SQLite             |
| **Face Recognition** | OpenCV, NumPy      |
| **Templates**        | Jinja2             |

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/sonalhans/face-attendance-app.git
cd face-attendance-app
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # For Mac/Linux
venv\Scripts\activate     # For Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the Application

```bash
python app.py
```

### 5️⃣ Open in Browser

Go to:

```
http://127.0.0.1:5000
```

---

## 🧑‍💻 Admin Access

* **Default Admin Login:**

  ```
  Username: admin
  Password: adminpass
  ```

---

## 📸 How It Works

1. **Register User:** Enter Roll No, Name, and capture the user’s image.
2. **Train Model:** The system automatically trains the recognition model.
3. **Mark Attendance:** When a registered face is recognized, attendance is logged automatically.
4. **View Attendance:** Check attendance records in the dashboard.

---

## 📂 Project Structure

```
face-attendance-app/
│
├── app.py                   # Main Flask application
├── database.db              # SQLite database
├── static/
│   ├── style.css            # Custom styling
│   └── background.png       # Background image
├── templates/
│   ├── layout.html          # Base layout with navigation
│   ├── login.html           # Admin login page
│   ├── dashboard.html       # Dashboard view
│   ├── users.html           # User registration page
│   ├── add_admin.html       # Add admin form
│   └── attendance_view.html # Attendance view page
└── README.md
```

---

## 💬 Authors

* **Sonal Hans**

---

## 🪄 Acknowledgements

* [Flask Documentation](https://flask.palletsprojects.com/)
* [Tailwind CSS](https://tailwindcss.com/)
* [OpenCV](https://opencv.org/)
* [NumPy](https://numpy.org/)

---

## 🖋️ License

This project is open-source and available under the [MIT License](LICENSE).

---

### 🌟 *"AI meets simplicity — a smart way to take attendance!"*
