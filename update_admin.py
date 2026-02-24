import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import CustomUser

def update_admin():
    username = 'shah123'
    password = 'Shah@786'
    email = 'admin@shahanwajkhan.com'
    
    user, created = CustomUser.objects.get_or_create(username=username)
    user.set_password(password)
    user.email = email
    user.role = 'Admin'
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    if created:
        print(f"User {username} created successfully.")
    else:
        print(f"User {username} updated successfully.")

if __name__ == "__main__":
    update_admin()
