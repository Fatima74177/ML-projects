# studentsPortal - Django Student Management System

A Django student management system with:

- Email-based authentication with role-based access (administrator, teacher, student)
- Full CRUD for students, teachers, courses, attendance, and grades
- A public landing page for visitors, and a live summary dashboard for signed-in users
- Postgres (Neon) in production, SQLite automatically for local development
- Light/dark theme, responsive layout with a mobile sidebar drawer
- Ready to deploy on Vercel

## What changed in this pass

- **Fixed a security bug**: the login form used to silently pre-fill the admin
  email/password for every visitor. Removed - the demo-account buttons on the
  login page are the only way to fill those in now, and only on click.
- **Fixed a security bug**: public self-registration used to let anyone pick
  "Administrator" as their role. Registration is now limited to
  teacher/student; create admin accounts with `createsuperuser` or promote a
  user from `/admin/`.
- Removed a stray `from flask.cli import load_dotenv` import from
  `config/settings.py` (Flask isn't part of this project) in favor of
  `python-dotenv` directly.
- Rewrote `requirements.txt` - the old file was UTF-16 encoded and full of
  unrelated packages from a global environment (Flask, google-genai,
  Werkzeug, etc.). It now only lists what this project uses.
- `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` now come from environment
  variables instead of being hardcoded, with safe local defaults.
- Fixed a crash where `ssl_require=True` was forced even for non-Postgres
  database URLs.
- Added a public landing page (`/`) for anonymous visitors instead of an
  immediate login redirect.
- Added a mobile sidebar drawer (hamburger toggle) and switched the base font
  to Inter for a more polished look.
- Added everything needed to deploy on Vercel: `vercel.json`, `api/index.py`,
  and WhiteNoise for static files (no separate build/collectstatic step
  required).
- Added `db/schema.sql` - the same schema `migrate` creates, as a plain SQL
  file you can run directly against Neon if you prefer that over Django's
  migration command.

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env if needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. If `DATABASE_URL` is not set in `.env`, the
app automatically uses a local `db.sqlite3` file - no Postgres needed for
local development.

### Demo accounts

The login page has quick-fill buttons for three demo accounts. These only
exist if you create them yourself (e.g. via `createsuperuser` for the admin
account, and `/accounts/register/` for the others) - they are not seeded
automatically:

- Admin: `admin@example.com` / `admin12345`
- Teacher: `teacher@example.com` / `teacher12345`
- Student: `student@example.com` / `student12345`

**If you deploy this with real student data, remove or change the demo
credentials panel in `accounts/templates/accounts/login.html` - showing
working login details on a public page is fine for a demo, not for
production data.**

## Database: using Neon (Postgres)

1. Create a project at [neon.tech](https://neon.tech) and copy its connection
   string (it looks like
   `postgresql://user:password@host/dbname?sslmode=require&channel_binding=require`).
2. Put it in `.env` as `DATABASE_URL=...` (local) and in your Vercel project's
   environment variables (production).
3. Create the schema either way:
   - **Recommended:** `python manage.py migrate` - Django creates every table
     and keeps track of what's applied.
   - **Alternative:** open `db/schema.sql` in Neon's SQL editor and run it
     once against a fresh database. It also records the migrations as
     applied so a later `python manage.py migrate` won't try to recreate
     anything. Don't do both on the same empty database.

## React dashboard widget

The interactive widget lives in `frontend/` and builds into `static/react/`:

```bash
cd frontend
npm install
npm run build
```

## Deploying to Vercel

1. **Push this project to a GitHub repo** (make sure `.env`, `db.sqlite3`,
   `node_modules/`, and `__pycache__/` are not committed - `.gitignore` and
   `.vercelignore` already exclude them).
2. **Set up your database** on [neon.tech](https://neon.tech) if you haven't
   already, and run the schema (see above) so the tables exist before your
   first deploy.
3. **Import the repo into Vercel** ([vercel.com/new](https://vercel.com/new)).
   Vercel will detect `vercel.json` and `api/index.py` automatically - no
   framework preset or build command needed.
4. **Add environment variables** in the Vercel project settings
   (Settings → Environment Variables):
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | your Neon connection string |
   | `DJANGO_SECRET_KEY` | a long random string (e.g. `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `*.vercel.app,your-custom-domain.com` |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app,https://your-custom-domain.com` |
5. **Deploy.** Vercel installs `requirements.txt` and serves the app through
   `api/index.py`. Static files (CSS/JS/icons) are served by WhiteNoise from
   inside the same process, so there's no separate static host to configure.
6. **Create your admin account** once the DB is reachable - either run
   `python manage.py createsuperuser` locally against the same
   `DATABASE_URL`, or insert a superuser row via the Neon SQL editor and set
   its password with Django's `make_password` helper.
7. Visit your `*.vercel.app` URL. You should land on the public landing page;
   sign in or register to reach the dashboard.

### Redeploying after model changes

Vercel doesn't run `migrate` for you. After changing models, run
`python manage.py makemigrations && python manage.py migrate` locally
(pointed at the same `DATABASE_URL` Vercel uses) before or after pushing your
code change, so the live database's schema matches what the deployed code
expects.

## Main URLs

- `/` - public landing page (signed out) / dashboard (signed in)
- `/accounts/login/`, `/accounts/register/`, `/accounts/profile/`
- `/students/`, `/teachers/`, `/courses/`, `/attendance/`, `/academics/`
- `/admin/` - Django admin site
