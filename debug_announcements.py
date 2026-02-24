import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import CustomUser, StudentProfile, Announcement

try:
    user = CustomUser.objects.get(username='aditya123')
    profile = user.student_profile
    print(f"User: {user.username}")
    print(f"Role: {user.role}")
    print(f"Department: {profile.department}")
    print(f"Semester: {profile.semester}")
    
    # Check announcements
    anns = Announcement.objects.all()
    print(f"\nTotal Announcements: {anns.count()}")
    for a in anns:
        print(f"Title: {a.title}")
        print(f"  Target Dept: {a.department}")
        print(f"  Target Sem: {a.semester}")
        
except Exception as e:
    print(f"Error: {e}")
