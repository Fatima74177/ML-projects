-- =====================================================================
-- Student Management System - PostgreSQL schema (for Neon)
-- =====================================================================
-- This file mirrors exactly what `python manage.py migrate` creates.
--
-- RECOMMENDED WORKFLOW (simplest, and what most people should do):
--   1. Set DATABASE_URL in your .env to your Neon connection string.
--   2. Run:  python manage.py migrate
--   That's it - Django creates every table below for you automatically,
--   and keeps its own bookkeeping table (django_migrations) in sync so
--   future `migrate` runs work correctly.
--
-- WHEN TO USE THIS FILE INSTEAD:
--   If you want to create the schema by hand in Neon's SQL editor
--   (e.g. to inspect it, seed a fresh database before your app connects,
--   or because you don't have local Python access), run this whole file
--   once against a NEW/EMPTY Neon database.
--
--   Afterwards, tell Django those migrations are already applied instead
--   of trying to re-run them (this file already inserts the required rows
--   into django_migrations at the bottom, so a normal
--   `python manage.py migrate` after this script will simply say
--   "No migrations to apply").
--
-- Do not run this file AND `python manage.py migrate` on an empty
-- database - pick one method. Running this file twice, or running it
-- after `migrate` has already created the tables, will fail with
-- "relation already exists" errors.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Django core tables (content types, permissions, groups, sessions,
-- migration bookkeeping). These exist regardless of your app's models.
-- ---------------------------------------------------------------------

CREATE TABLE django_content_type (
    id            SERIAL PRIMARY KEY,
    app_label     VARCHAR(100) NOT NULL,
    model         VARCHAR(100) NOT NULL,
    CONSTRAINT django_content_type_app_label_model_uniq UNIQUE (app_label, model)
);

CREATE TABLE auth_permission (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    content_type_id INTEGER NOT NULL REFERENCES django_content_type (id) DEFERRABLE INITIALLY DEFERRED,
    codename        VARCHAR(100) NOT NULL,
    CONSTRAINT auth_permission_content_type_id_codename_uniq UNIQUE (content_type_id, codename)
);
CREATE INDEX auth_permission_content_type_id_idx ON auth_permission (content_type_id);

CREATE TABLE auth_group (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_group_permissions (
    id            SERIAL PRIMARY KEY,
    group_id      INTEGER NOT NULL REFERENCES auth_group (id) DEFERRABLE INITIALLY DEFERRED,
    permission_id INTEGER NOT NULL REFERENCES auth_permission (id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT auth_group_permissions_group_id_permission_id_uniq UNIQUE (group_id, permission_id)
);
CREATE INDEX auth_group_permissions_group_id_idx ON auth_group_permissions (group_id);
CREATE INDEX auth_group_permissions_permission_id_idx ON auth_group_permissions (permission_id);

CREATE TABLE auth_user (
    id           SERIAL PRIMARY KEY,
    password     VARCHAR(128) NOT NULL,
    last_login   TIMESTAMPTZ NULL,
    is_superuser BOOLEAN NOT NULL,
    username     VARCHAR(150) NOT NULL UNIQUE,
    first_name   VARCHAR(150) NOT NULL,
    last_name    VARCHAR(150) NOT NULL,
    email        VARCHAR(254) NOT NULL,
    is_staff     BOOLEAN NOT NULL,
    is_active    BOOLEAN NOT NULL,
    date_joined  TIMESTAMPTZ NOT NULL
);

CREATE TABLE auth_user_groups (
    id       SERIAL PRIMARY KEY,
    user_id  INTEGER NOT NULL REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED,
    group_id INTEGER NOT NULL REFERENCES auth_group (id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT auth_user_groups_user_id_group_id_uniq UNIQUE (user_id, group_id)
);
CREATE INDEX auth_user_groups_user_id_idx ON auth_user_groups (user_id);
CREATE INDEX auth_user_groups_group_id_idx ON auth_user_groups (group_id);

CREATE TABLE auth_user_user_permissions (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED,
    permission_id INTEGER NOT NULL REFERENCES auth_permission (id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT auth_user_user_permissions_user_id_permission_id_uniq UNIQUE (user_id, permission_id)
);
CREATE INDEX auth_user_user_permissions_user_id_idx ON auth_user_user_permissions (user_id);
CREATE INDEX auth_user_user_permissions_permission_id_idx ON auth_user_user_permissions (permission_id);

CREATE TABLE django_admin_log (
    id             SERIAL PRIMARY KEY,
    action_time    TIMESTAMPTZ NOT NULL,
    object_id      TEXT NULL,
    object_repr    VARCHAR(200) NOT NULL,
    action_flag    SMALLINT NOT NULL CHECK (action_flag >= 0),
    change_message TEXT NOT NULL,
    content_type_id INTEGER NULL REFERENCES django_content_type (id) DEFERRABLE INITIALLY DEFERRED,
    user_id        INTEGER NOT NULL REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX django_admin_log_content_type_id_idx ON django_admin_log (content_type_id);
CREATE INDEX django_admin_log_user_id_idx ON django_admin_log (user_id);

CREATE TABLE django_session (
    session_key  VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date  TIMESTAMPTZ NOT NULL
);
CREATE INDEX django_session_expire_date_idx ON django_session (expire_date);

CREATE TABLE django_migrations (
    id      BIGSERIAL PRIMARY KEY,
    app     VARCHAR(255) NOT NULL,
    name    VARCHAR(255) NOT NULL,
    applied TIMESTAMPTZ NOT NULL
);


-- ---------------------------------------------------------------------
-- App tables, in dependency order (teachers/students before the tables
-- that reference them).
-- ---------------------------------------------------------------------

-- teachers.Teacher
CREATE TABLE teachers_teacher (
    id          BIGSERIAL PRIMARY KEY,
    teacher_id  VARCHAR(20) NOT NULL UNIQUE,
    full_name   VARCHAR(120) NOT NULL,
    email       VARCHAR(254) NOT NULL UNIQUE,
    department  VARCHAR(120) NOT NULL,
    phone       VARCHAR(20) NOT NULL DEFAULT '',
    status      VARCHAR(20) NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'inactive')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- students.Student
CREATE TABLE students_student (
    id             BIGSERIAL PRIMARY KEY,
    student_id     VARCHAR(20) NOT NULL UNIQUE,
    full_name      VARCHAR(120) NOT NULL,
    email          VARCHAR(254) NOT NULL UNIQUE,
    phone          VARCHAR(20) NOT NULL DEFAULT '',
    program        VARCHAR(120) NOT NULL,
    year           VARCHAR(20) NOT NULL,
    date_of_birth  DATE NULL,
    address        TEXT NOT NULL DEFAULT '',
    status         VARCHAR(20) NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active', 'inactive', 'graduated')),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- accounts.Profile (one-to-one with auth_user)
CREATE TABLE accounts_profile (
    id       BIGSERIAL PRIMARY KEY,
    role     VARCHAR(20) NOT NULL DEFAULT 'student'
             CHECK (role IN ('administrator', 'teacher', 'student')),
    phone    VARCHAR(20) NOT NULL DEFAULT '',
    address  TEXT NOT NULL DEFAULT '',
    user_id  INTEGER NOT NULL UNIQUE REFERENCES auth_user (id) DEFERRABLE INITIALLY DEFERRED
);

-- courses.Course (teacher is optional - SET NULL if the teacher is removed)
CREATE TABLE courses_course (
    id           BIGSERIAL PRIMARY KEY,
    course_code  VARCHAR(20) NOT NULL UNIQUE,
    title        VARCHAR(150) NOT NULL,
    schedule     VARCHAR(120) NOT NULL,
    credits      SMALLINT NOT NULL DEFAULT 3 CHECK (credits >= 0),
    capacity     INTEGER NOT NULL DEFAULT 0 CHECK (capacity >= 0),
    description  TEXT NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    teacher_id   BIGINT NULL REFERENCES teachers_teacher (id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX courses_course_teacher_id_idx ON courses_course (teacher_id);

-- attendance.Attendance (deleting a student/course cascades to their records)
CREATE TABLE attendance_attendance (
    id               BIGSERIAL PRIMARY KEY,
    attendance_date  DATE NOT NULL,
    status           VARCHAR(20) NOT NULL DEFAULT 'present'
                     CHECK (status IN ('present', 'absent', 'late')),
    note             VARCHAR(255) NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    course_id        BIGINT NOT NULL REFERENCES courses_course (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    student_id       BIGINT NOT NULL REFERENCES students_student (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX attendance_attendance_course_id_idx ON attendance_attendance (course_id);
CREATE INDEX attendance_attendance_student_id_idx ON attendance_attendance (student_id);

-- academics.Grade (deleting a student/course cascades to their grades)
CREATE TABLE academics_grade (
    id          BIGSERIAL PRIMARY KEY,
    exam_name   VARCHAR(120) NOT NULL,
    marks       NUMERIC(5, 2) NOT NULL,
    grade       VARCHAR(3) NOT NULL,
    remarks     VARCHAR(255) NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    course_id   BIGINT NOT NULL REFERENCES courses_course (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    student_id  BIGINT NOT NULL REFERENCES students_student (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX academics_grade_course_id_idx ON academics_grade (course_id);
CREATE INDEX academics_grade_student_id_idx ON academics_grade (student_id);


-- ---------------------------------------------------------------------
-- Tell Django these migrations are already applied, so a subsequent
-- `python manage.py migrate` does nothing instead of trying (and
-- failing) to recreate these tables. Skip this block if you plan to
-- run `python manage.py migrate` from an empty database instead of
-- this file.
-- ---------------------------------------------------------------------

INSERT INTO django_migrations (app, name, applied) VALUES
    ('students', '0001_initial', NOW()),
    ('teachers', '0001_initial', NOW()),
    ('courses', '0001_initial', NOW()),
    ('academics', '0001_initial', NOW()),
    ('contenttypes', '0001_initial', NOW()),
    ('auth', '0001_initial', NOW()),
    ('accounts', '0001_initial', NOW()),
    ('admin', '0001_initial', NOW()),
    ('admin', '0002_logentry_remove_auto_add', NOW()),
    ('admin', '0003_logentry_add_action_flag_choices', NOW()),
    ('attendance', '0001_initial', NOW()),
    ('contenttypes', '0002_remove_content_type_name', NOW()),
    ('auth', '0002_alter_permission_name_max_length', NOW()),
    ('auth', '0003_alter_user_email_max_length', NOW()),
    ('auth', '0004_alter_user_username_opts', NOW()),
    ('auth', '0005_alter_user_last_login_null', NOW()),
    ('auth', '0006_require_contenttypes_0002', NOW()),
    ('auth', '0007_alter_validators_add_error_messages', NOW()),
    ('auth', '0008_alter_user_username_max_length', NOW()),
    ('auth', '0009_alter_user_last_name_max_length', NOW()),
    ('auth', '0010_alter_group_name_max_length', NOW()),
    ('auth', '0011_update_proxy_permissions', NOW()),
    ('auth', '0012_alter_user_first_name_max_length', NOW()),
    ('sessions', '0001_initial', NOW());

-- After this, create an administrator account with:
--   python manage.py createsuperuser
-- then log in at /admin/ and (optionally) create matching accounts_profile
-- rows, or just register normally at /accounts/register/ for
-- teacher/student accounts.
