from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('timetable/', views.manage_timetable, name='manage_timetable'),
    path('placements/', views.manage_placements, name='manage_placements'),
    path('departments/', views.manage_departments, name='manage_departments'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('students/', views.manage_students, name='manage_students'),
    path('faculty/', views.manage_faculty, name='manage_faculty'),
    path('complaints/', views.manage_complaints, name='manage_complaints'),
    path('id-cards/', views.manage_id_cards, name='manage_id_cards'),
    path('id-cards/generate/<str:user_role>/<int:user_id>/', views.generate_id_card, name='generate_id_card'),
    path('announcements/', views.manage_announcements, name='manage_announcements'),
    path('announcements/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    path('fees/', views.manage_fees, name='manage_fees'),
    path('results/', views.manage_results, name='manage_results'),
    path('results/delete/<int:record_id>/', views.delete_grade_record, name='delete_grade_record'),
    path('requests/', views.manage_requests, name='manage_requests'),
]
