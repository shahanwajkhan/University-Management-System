# 🏛️ University Management System (UMS)

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-6.0.2-green?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Database](https://img.shields.io/badge/database-SQLite%20%7C%20PostgreSQL-lightgrey?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Deployment](https://img.shields.io/badge/deployment-Vercel%20%2F%20Gunicorn-darkgreen?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A next-generation digital administration ecosystem built with Django 6.0 for modern academic institutions. UMS bridges administrators, educators, and students under a single, highly-secure, role-restricted dashboard infrastructure. It streamlines academic operations, automates attendance checking, organizes timetables, calculates grades, processes online payments, and handles corporate placement drives.

---

## 🚀 Key Portals & Role-Based Workspaces

### 🔑 1. Admin Portal (Supervisory Console)
The central command center for University Administrators and Head of Departments (HODs) to oversee system health, manage rosters, verify payments, and authorize leaves.
- **Global Analytical Dashboard**: Visual cards featuring system statistics using optimized database aggregation APIs.
- **Academic Control**: Full CRUD management of student/faculty roster profiles, departments, and subjects.
- **Financial Audit Desk**: Review, approve, or reject student payment records and manage fee balances.
- **Centralized Timetable Creator**: Direct and delegate schedules for both students and faculty.
- **Campus Announcement System**: Broadcast campus-wide official notices.
- **Service Request & Complaint Center**: Resolve leave approvals, bonafide certificate requests, and student complaints.
- *Detailed Architecture: Check the [Admin Portal Guide](./admin_portal_guide.md).*

### 🧑‍🏫 2. Faculty Workspace (Instructional Portal)
A secure portal designed for professors and academic advisors to handle classes, student performance, and lecture resources.
- **Department-Isolated Workspace**: Access restricted strictly to the instructor's designated department.
- **Automated Grading Engine**: Simple marks insertion with automated grade calculations (O, A+, A, B+, B, C, P, F) and grade points based on custom thresholds.
- **Real-Time Attendance Register**: Seamless interface to mark present/absent student attendance status.
- **Material Repository**: Publish PDFs, files, and lecture slides directly to subjects.
- **Targeted Notices**: Send semester/department specific announcements to class groups.
- *Detailed Architecture: Check the [Faculty Portal Guide](./faculty_portal_guide.md).*

### 🎓 3. Student Workspace (Academic Workspace)
An intuitive, modern workspace designed for students to track their academic journeys, attendance, fee transactions, and request documents.
- **Interactive Attendance Analytics**: Visual display of subject attendance percentages with color-coded warnings (e.g., `< 75%` danger zones).
- **Online Fees & Payments**: File payment records, enter transaction IDs, and attach receipts for admin review.
- **CGPA & Grades Overview**: Monitor academic results across current and past semesters.
- **Digital Noticeboard**: View global notices and department announcements.
- **Service Desk**: Submit leave requests and log academic or infrastructure complaints.
- *Detailed Architecture: Check the [Student Portal Guide](./student_portal_guide.md).*

---

## 📷 Portal Screenshots & Walkthroughs

<details>
<summary><b>🖥️ Unified Login & Admin Dashboards (Click to Expand)</b></summary>
<br>

| Multi-Role Login Portal | Admin Executive Command Center |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/f135d46c-17b5-44e2-8ed3-81d4df884d57" width="100%"/> | <img src="https://github.com/user-attachments/assets/5cab9ac4-3cd2-4f52-bcd6-5924c2700e91" width="100%"/> |

| Core Departmental Statistics | Centralized System Oversight |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/ebdaa0e2-b611-4a19-a7e2-32aae2a54197" width="100%"/> | <img src="https://github.com/user-attachments/assets/6a2533cd-94dd-4b62-b1b7-a0ea56bef2b7" width="100%"/> |

</details>

<details>
<summary><b>🧑‍🏫 Faculty Portal & Course Operations (Click to Expand)</b></summary>
<br>

| Subject Assignments | Student Roster Management |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/6437e55a-c5ea-4798-9250-000a85adbfc7" width="100%"/> | <img src="https://github.com/user-attachments/assets/0261776b-3389-45a1-9cc6-3911cf54c9d3" width="100%"/> |

| Academic Grading Interface | Learning Materials Repository |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/2c84589f-76b6-4b94-9b76-835a2bdc4290" width="100%"/> | <img src="https://github.com/user-attachments/assets/f303beb4-2f14-419f-987c-5d5344427685" width="100%"/> |

</details>

<details>
<summary><b>🎓 Student Dashboard & Academic Tracking (Click to Expand)</b></summary>
<br>

| Attendance Records Analytics | Semester Timetable |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/8ce5018e-0c0d-49c1-bc95-d4311807f1a4" width="100%"/> | <img src="https://github.com/user-attachments/assets/088bacde-0ce4-4c9d-ac34-42a1b3cbe6e0" width="100%"/> |

| Fee & Payment Processing | Global & Internal Announcements |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/2c49a8fd-3bbc-4ae6-b877-5e4a05a804ec" width="100%"/> | <img src="https://github.com/user-attachments/assets/f3b693fb-0e10-4054-9c05-50decd70928e" width="100%"/> |

</details>

---

## 🛠️ Tech Stack & Dependencies

- **Backend**: Django 6.0.2, Python 3.10+
- **Frontend**: Bootstrap 5 (CSS & JS Components), Custom Vanilla CSS modules, Vanilla JavaScript
- **Database**: SQLite (Development), PostgreSQL-Ready (Production via `dj-database-url` / `psycopg2-binary`)
- **Static Assets**: WhiteNoise (efficient caching & serving)
- **Deployment**: Vercel configuration (`vercel.json`, `build_files.sh`)

---

## 📂 Project Structure

```text
University-Management-System/
│
├── core/                       # Shared models, global utilities & user authentication
│   ├── models.py               # CustomUser, Department, Subject, Announcement, Notification
│   ├── views.py                # Role selection and baseline authorization gates
│   └── urls.py                 # Account navigation routing
│
├── student/                    # Student-specific operations & interfaces
│   ├── models.py               # StudentProfile, PaymentRecord, StudentRequest, Complaint
│   └── views.py                # Attendance percentages, results, and fee logs
│
├── faculty/                    # Instruction & grading modules
│   ├── models.py               # FacultyProfile, AttendanceRecord, GradeRecord, LearningMaterial, TimeTableRecord
│   └── views.py                # Attendance posting, grading tables, syllabus materials
│
├── organization/               # Administrative controls & Placement Drives
│   ├── models.py               # PlacementDrive, PlacementApplication
│   └── views.py                # System-wide reporting, requests administration, drive sign-ups
│
├── templates/                  # Integrated Django HTML Templates (extended from base.html)
│   ├── core/                   # Role selection, login pages
│   ├── student/                # Student dashboard, attendance, requests, grades
│   ├── faculty/                # Faculty class panels, grades portal, attendance sheets
│   └── organization/           # Administrative panels, placement drives manager
│
├── ums_project/                # Global Settings & WSGI configuration
│   ├── settings.py             # Global configurations, WhiteNoise & production switches
│   └── urls.py                 # Core routing registry
│
├── requirements.txt            # System dependencies manifest
├── manage.py                   # Django CLI executable manager
└── vercel.json                 # Vercel deployment pipeline instructions
```

---

## ⚙️ Local Development Setup

Follow these steps to run the University Management System on your local system:

### 1. Prerequisites
Ensure you have the following installed:
- Python 3.10 or higher
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/shahanwajkhan/University-Management-System.git
cd University-Management-System
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Admin / Superuser
Create your admin profile to configure departments and manage accounts:
```bash
python create_admin.py
```
*Follow the interactive prompts to set up your username, email, and password.*

### 7. Seed Sample Academic Data
To test the portal with pre-populated datasets (Realistic subjects, timetables, and past 30 days of attendance):
```bash
python seed_timetable.py
```

### 8. Run the Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000` on your browser to explore the portals.

---

## 🌐 Production Deployment (Vercel)

The system is configured for direct deployment to Vercel using Serverless Functions.

1. **Install Vercel CLI**: `npm i -g vercel`
2. **Link Project**: `vercel link`
3. **Set Environment Variables**: Configure `.env` items on your Vercel Dashboard.
4. **Deploy**: `vercel --prod`

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
