import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import CustomUser

students = CustomUser.objects.filter(role='Student')
print(f"Total Students: {students.count()}")
for s in students:
    profile = s.student_profile
    print(f"User: {s.username}, Dept: {profile.department}, Sem: {profile.semester}")
