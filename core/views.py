from django.shortcuts import render

def home(request):
    return render(request, 'core/index.html')

def role_selection(request):
    return render(request, 'core/role_selection.html')

def about(request):
    return render(request, 'core/about.html')

def services(request):
    return render(request, 'core/services.html')

def portfolio(request):
    return render(request, 'core/portfolio.html')

def team(request):
    return render(request, 'core/team.html')

def contact(request):
    return render(request, 'core/contact.html')

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from .models import CustomUser

def login_page(request, role):
    # Role can be 'student', 'faculty', 'admin'
    context = {
        'role': role.capitalize(),
    }

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'signup':
            # Handle Signup
            username = request.POST.get('username', '').strip()
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered.")
            elif CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username is already taken.")
            else:
                user = CustomUser.objects.create_user(
                    username=username,
                    full_name=full_name,
                    email=email,
                    password=password,
                    role=role.capitalize(),
                    is_active=True  # Activated immediately
                )
                
                messages.success(request, f"Account created successfully for {username}! You can now log in.")
                return redirect('login_page', role=role)
                
        elif action == 'login':
            # Handle Login
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.role == 'Student':
                    return redirect('student_dashboard')
                elif user.role == 'Faculty':
                    return redirect('faculty_dashboard')
                elif user.role == 'Admin':
                    return redirect('admin_dashboard')
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
            
    return render(request, 'core/login_page.html', context)

def verify_email(request, uidb64, token):
    # This view is now deactivated but kept for URL consistency if needed
    messages.info(request, "Email verification is no longer required. You can log in directly.")
    return redirect('home')
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')
