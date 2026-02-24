# University Management System (UMS)
## Student Portal - Comprehensive Architecture & Feature Guide

This document outlines the detailed features, structure, and Django backend implementation strategies utilized in the UMS **Student Portal**.

---

### 1. Overview of the Student Portal
The Student Portal is a robust, isolated ecosystem designed specifically for enrolled students. It allows them to view their academic records, track attendance, manage fees, request leave, and stay updated with official announcements.

**Key Architecture Principles:**
- **Role-Based Access Control (RBAC):** Django custom middleware and decorators (`@role_required('Student')`) ensure that only users with the `Student` role can access these views.
- **Session Security:** Every route validates the active session against the `User` model, preventing unauthorized URL traversal.
- **Responsive UI:** The frontend leverages Bootstrap 5 to guarantee functionality across all device form factors (Mobile, Tablet, Desktop).

---

### 2. Core Features & Implementation

#### A. Secure Authentication & Dashboard Landing
- **Feature:** Secure login via `/select-role` using a unified credentials system.
- **Django Implementation:**
  - **Models:** Inherits from a custom Abstract `User` model linked to a detailed `Student` profile model containing fields like `enrollment_number`, `department`, `semester`, and `blood_group`.
  - **Views:** The `dashboard` view fetches immediate contextual data—like today's classes and recent announcements—by running selective ORM queries `Announcement.objects.filter(target_audience='Students')`.
  - **Templates:** Renders `student/dashboard.html` extending a unified `dashboard_base.html`.

#### B. Academic Results Tracking (CGPA)
- **Feature:** Students can view their semester-wise grades and cumulatively tracked CGPA.
- **Django Implementation:**
  - **Models:** Uses a `Result` model uniquely linking a `Student` `ForeignKey` to a `Subject` and `Semester`.
  - **Views:** The views calculate the overarching CGPA dynamically or pull pre-cached values from the database to present to the user.
  - **Template Logic:** Uses Django template tags (`{% for result in results %}`) to iterate through the data dynamically inside `results.html` using a clean Bootstrap table format.

#### C. Attendance Management
- **Feature:** Real-time visibility into subject-wise attendance percentages, highlighting alerts for low attendance.
- **Django Implementation:**
  - **Models:** An `Attendance` model tracking total lectures delivered versus attended per student.
  - **Dynamic Calculation:** The `views.py` calculates percentage dynamically `(attended / total) * 100` before shipping the context to the template.
  - **UI Indicators:** Badge styling shifts dynamically (e.g., Red for < 75%, Green for > 85%) using Django conditionals: `{% if attendance_percent < 75 %}bg-danger{% endif %}`.

#### D. Fee & Finance Processing
- **Feature:** Allows students to view pending dues, track payment histories, and access digital receipts.
- **Django Implementation:**
  - **Models:** `FeeRecord` or `Payment` models track transaction ID, date, status (Pending, Success, Failed), and due amounts.
  - **Views:** The `fees` view filters records specifically for the logged-in student `request.user.student_profile`.

#### E. Leave Requests & Approvals
- **Feature:** Students can formally request leave (Sick, Urgent, Event) and track the approval pipeline (Pending -> Approved/Rejected).
- **Django Implementation:**
  - **Models:** `LeaveRequest` model storing `start_date`, `end_date`, `reason`, and an `AdminComment` field.
  - **Forms:** Utilizes Django Forms (`forms.py`) to handle POST requests securely, sanitizing inputs before saving them via `form.save()`.

#### F. Personalized Announcements
- **Feature:** A dedicated notice board displaying global campus news and department-specific alerts.
- **Django Implementation:**
  - **Query Targeting:** The backend intelligently filters `Announcement.objects.filter(department=student.department)` so students aren't spammed with irrelevant notices.

---

### 3. Understanding the Django Request-Response Lifecycle
When a student interacts with the portal, the application executes the following flow:
1. **URL Routing:** `urls.py` captures the request (e.g., `/student/attendance/`) and passes it to the corresponding view.
2. **Middleware/Auth:** Django verifies that `request.user.is_authenticated` and has the `Student` role.
3. **Database (ORM):** `views.py` queries the specific Django Models (e.g., SQLite/PostgreSQL) strictly filtering by `student_id`.
4. **Context Assembly:** The fetched data is bundled into a Python dictionary.
5. **Template Rendering:** The Jinja-style Django templating engine `{% ... %}` dynamically generates the final HTML inside templates like `fees.html` or `results.html` and returns it to the browser.

---
*Created dynamically for the UMS Development Team.*
