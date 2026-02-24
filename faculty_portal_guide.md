# University Management System (UMS)
## Faculty Portal - Comprehensive Architecture & Feature Guide

This document outlines the detailed features, structure, and Django backend implementation strategies utilized in the UMS **Faculty Portal**.

---

### 1. Overview of the Faculty Portal
The Faculty Portal acts as a digital dashboard for professors and instructors. It provides a secure, organized environment to manage students, record daily attendance, publish academic results, and broadcast announcements.

**Key Architecture Principles:**
- **Role-Based Access Control (RBAC):** Django custom decorators limit views to users with the `Faculty` role.
- **Isolated Data Access:** Faculty members can only view data, students, and courses mapped to their specific departments and subjects.
- **Interactive Dashboards:** Built using Bootstrap 5, featuring real-time statistics cards powered by targeted Django ORM aggregations.

---

### 2. Core Features & Implementation

#### A. Secure Authentication & Faculty Dashboard
- **Feature:** Secure login via `/select-role`, routing faculty to a dedicated dashboard presenting a snapshot of their daily responsibilities.
- **Django Implementation:**
  - **Models:** Inherits from the custom Abstract `User` model, paired with a detailed `Faculty` profile model (containing `employee_id`, `department`, `designation`).
  - **Views:** The `dashboard` view fetches immediate contextual stats (Total Students, Courses Handled) by running counts like `Student.objects.filter(department=faculty.department).count()`.
  - **Templates:** Renders `faculty/dashboard.html` extending the clean `dashboard_base.html`.

#### B. Subject & Student Management
- **Feature:** Faculty can view the subjects they teach and the list of enrolled students.
- **Django Implementation:**
  - **Models:** Uses `Subject` and `FacultySubject` mappings to link professors strictly to their designated classes.
  - **Views:** When a faculty member clicks "My Students", the view filters students enrolled in the specific semesters and departments tied to the faculty's active subjects.
  - **Dynamic Interactivity:** Fetches data via optimized queries (`select_related` and `prefetch_related`) to prevent N+1 query bottlenecks in Django.

#### C. Real-Time Attendance Marking
- **Feature:** An interactive portal to mark and update daily student attendance (Present/Absent).
- **Django Implementation:**
  - **Models:** Utilizes the `Attendance` model to record daily lecture counts and attended lectures per student.
  - **Forms/Views:** Uses a combination of Django Forms and AJAX-ready endpoints. The backend receives a list of student IDs mapped to 'status' arrays via `POST` requests, iterating through and safely updating `Attendance.objects.get_or_create()`.
  - **UI Indicators:** Toast notifications and JavaScript handle the frontend interactions to ensure smooth "Attendance Saved" popups.

#### D. Results Publishing
- **Feature:** A dedicated interface to review, enter, and finalize semester grades.
- **Django Implementation:**
  - **Data Handling:** Pulls the `Result` objects linked to the subjects managed by the logged-in faculty.
  - **Security:** Faculty can only edit grades for their specifically assigned subject and semester to prevent unauthorized grade manipulation.

#### E. Broadcasting Announcements
- **Feature:** Faculty can instantly publish notices, assignments, or alerts to their designated students.
- **Django Implementation:**
  - **Models:** The `Announcement` model includes a `target_audience`, `department`, and `semester` field.
  - **Views:** A specialized `create_announcement` view captures the form data. Crucially, the view automatically stamps the `author` field with `request.user.faculty_profile`, ensuring accountability.
  - **Filtering:** When posted, these announcements are dynamically routed to the dashboards of the target students based on matching departments.

---

### 3. Understanding the Django Request-Response Lifecycle (Faculty Context)
When an instructor interacts with the portal, the application executes the following flow:
1. **URL Routing:** `urls.py` captures requests like `/faculty/manage_attendance/`.
2. **Middleware/Auth:** Django validates that the session token belongs to an active user with `is_faculty=True`.
3. **Database (ORM):** `views.py` queries the SQLite/PostgreSQL database strictly isolating data using `request.user.faculty_profile.department`.
4. **Context Processing:** Aggregated data (attendance lists, grade arrays) are sanitized and packed into the context dictionary.
5. **Template Rendering:** Jinja logic outputs the custom Bootstrap tables and forms, returning the fully assembled HTML DOM directly to the browser.

---
*Created dynamically for the UMS Development Team.*
