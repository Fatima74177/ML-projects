# studentsPortal Django Student Management System

This project is a Python/Django student management system with:

- authentication
- student, teacher, course, attendance, and grade management
- dashboard summaries
- SQLite database support
- a React dashboard widget for live search and quick insights

## Run locally

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open the local address shown by Django, usually `http://127.0.0.1:8000/`.

## Default logins

- Admin: `admin@example.com` / `admin12345`
- Teacher: `teacher@example.com` / `teacher12345`
- Student: `student@example.com` / `student12345`

## React frontend

The interactive dashboard widget lives in `frontend/` and builds into `static/react/`.

```powershell
cd frontend
npm.cmd install
npm.cmd run build
```

## Main URLs

- `/accounts/login/`
- `/accounts/register/`
- `/`
- `/students/`
- `/teachers/`
- `/courses/`
- `/attendance/`
- `/academics/`
