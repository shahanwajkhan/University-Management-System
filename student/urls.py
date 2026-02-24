from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('materials/', views.learning_materials, name='learning_materials'),
    path('results/', views.student_results, name='student_results'),
    path('placement/', views.placement_portal, name='placement_portal'),
    path('fees/', views.fee_portal, name='fee_portal'),
    path('requests/', views.service_requests, name='service_requests'),
    path('grievance/', views.grievance_portal, name='grievance_portal'),
    path('timetable/', views.student_timetable, name='student_timetable'),
    path('api/advisor/', views.academic_advisor_api, name='advisor_api'),
    path('profile/', views.student_profile, name='student_profile'),
    path('id-card/', views.download_id_card, name='download_id_card'),
]
