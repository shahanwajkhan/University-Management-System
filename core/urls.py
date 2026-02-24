from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('team/', views.team, name='team'),
    path('contact/', views.contact, name='contact'),
    path('role-selection/', views.role_selection, name='role_selection'),
    path('login/<str:role>/', views.login_page, name='login_page'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('logout/', views.logout_user, name='logout'),
]
