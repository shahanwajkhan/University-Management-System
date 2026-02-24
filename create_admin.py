"""
Script to create a Django superuser for admin access
Run this with: python create_admin.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import CustomUser

def create_admin():
    username = input("Enter username for admin: ").strip()
    email = input("Enter email (optional): ").strip() or ""
    password = input("Enter password: ").strip()
    
    if not username or not password:
        print("Username and password are required!")
        return
    
    # Check if user exists
    if CustomUser.objects.filter(username=username).exists():
        user = CustomUser.objects.get(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.role = 'Admin'
        if email:
            user.email = email
        user.save()
        print(f"\n✓ Updated existing user '{username}' to superuser/admin")
    else:
        # Create new superuser
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='Admin',
            is_staff=True,
            is_superuser=True
        )
        print(f"\n✓ Created new superuser '{username}'")
    
    print(f"\nYou can now login to Django admin at: http://127.0.0.1:8000/admin/")
    print(f"Username: {username}")

if __name__ == '__main__':
    create_admin()
