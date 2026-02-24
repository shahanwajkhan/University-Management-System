import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import Announcement, StudentProfile, Department

with open('debug_output.txt', 'w') as f:
    f.write("=== DEPARTMENTS ===\n")
    for d in Department.objects.all():
        f.write(f"ID: {d.id}, Name: {d.name}\n")

    f.write("\n=== STUDENT PROFILES ===\n")
    for s in StudentProfile.objects.all():
        f.write(f"User: {s.user.username}, DeptID: {s.department.id if s.department else 'None'}, Sem: {s.semester}\n")

    f.write("\n=== ANNOUNCEMENTS ===\n")
    for a in Announcement.objects.all():
        f.write(f"Title: {a.title}, DeptID: {a.department.id}, Sem: {a.semester}, CreatedBy: {a.faculty.user.username}\n")

    f.write("\n=== POTENTIAL MATCHES ===\n")
    for s in StudentProfile.objects.all():
        matches = Announcement.objects.filter(department=s.department, semester=s.semester)
        f.write(f"Student {s.user.username} matches {matches.count()} announcements.\n")
