from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('mark-attendance/<int:subject_id>/', views.mark_attendance, name='mark_attendance'),
    path('edit-attendance/', views.edit_attendance, name='edit_attendance'),
    path('view-attendance/<int:subject_id>/', views.view_attendance_percentage, name='view_attendance_percentage'),
    path('export-attendance/<int:subject_id>/', views.export_attendance_pdf, name='export_attendance_pdf'),
    path('upload-material/', views.upload_material, name='upload_material'),
    path('edit-material/<int:material_id>/', views.edit_material, name='edit_material'),
    path('delete-material/<int:material_id>/', views.delete_material, name='delete_material'),
    path('timetable/', views.faculty_timetable, name='faculty_timetable'),
    path('profile/', views.faculty_profile, name='faculty_profile'),
    path('id-card/', views.download_faculty_id_card, name='download_faculty_id_card'),
    path('announcements/', views.manage_announcements, name='faculty_announcements'),
    path('announcements/delete/<int:announcement_id>/', views.delete_announcement, name='faculty_delete_announcement'),
    path('complaints/', views.manage_complaints, name='faculty_complaints'),
    path('complaints/update/<int:complaint_id>/', views.update_complaint, name='faculty_update_complaint'),
]
