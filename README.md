📝 Online Exam System

An intuitive online exam platform to create, manage, and take exams effortlessly.
Admins can manage exams & students, while students can take exams and view instant results.

🚀 Features
Admin

🎯 Create and manage subjects, exams, and questions

✅ Add MCQs, True/False, or short-answer questions

📊 View and export student performance reports

Student

📝 Register and take exams online

⏱ Timed exams with automatic submission

📈 View results and performance history

General

🔒 Secure authentication

📱 Responsive design for mobile and desktop

💾 Lightweight and easy to deploy

🛠 Tech Stack
Layer	Technology
Backend	Django (Python)
Frontend	HTML, CSS, JavaScript
Database	SQLite (default), optional: PostgreSQL/MySQL
Libraries	Django REST framework (optional)
⚡ Quick Start
1️⃣ Clone the repo
git clone https://github.com/yourusername/online-exam-system.git
cd online-exam-system

2️⃣ Setup virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Apply migrations
python manage.py makemigrations
python manage.py migrate

5️⃣ Create superuser
python manage.py createsuperuser

6️⃣ Run the server
python manage.py runserver


🌐 Access: http://127.0.0.1:8000

🛠 Admin panel: http://127.0.0.1:8000/admin

📂 Project Structure
online_exam_system/
│
├── exam_app/               # Main Django app
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   ├── static/             # CSS, JS, images
│   ├── models.py           # Database models
│   ├── views.py            # Application views
│   ├── urls.py             # App URLs
│   └── admin.py            # Admin configurations
│
├── online_exam_system/     # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies

🌟 Future Enhancements

🕑 Timed exams with auto-submit

🔀 Randomized questions for each student

📊 Analytics dashboard with graphs

📱 Mobile app integration

🖼 Support for file uploads (subjective answers)

🤝 Contributing

Contributions are welcome!

Fork the repo

Create a branch (git checkout -b feature-name)

Commit your changes (git commit -m "Add new feature")

Push to the branch (git push origin feature-name)

Open a Pull Request
