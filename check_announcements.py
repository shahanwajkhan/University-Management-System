import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import Announcement, StudentProfile, Department

print("--- DEPARTMENTS ---")
for d in Department.objects.all():
    print(f"ID: {d.id}, Name: {d.name}")

print("\n--- STUDENT PROFILES ---")
for s in StudentProfile.objects.all():
    print(f"User: {s.user.username}, Dept: {s.department.name if s.department else 'None'} (ID: {s.department.id if s.department else 'N/A'}), Sem: {s.semester}")

print("\n--- ANNOUNCEMENTS ---")
for a in Announcement.objects.all():
    print(f"Title: {a.title}, Dept: {a.department.name} (ID: {a.department.id}), Sem: {a.semester}, Faculty: {a.faculty.user.username}")

print("\n--- MATCHING CHECK ---")
# Check if any student matches any announcement
for s in StudentProfile.objects.all():
    matches = Announcement.objects.filter(department=s.department, semester=s.semester)
    print(f"Student {s.user.username} matches {matches.count()} announcements.")
