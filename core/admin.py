from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, Subject, Announcement, Notification
from student.models import StudentProfile, PaymentRecord, StudentRequest, Complaint
from faculty.models import FacultyProfile, AttendanceRecord, GradeRecord, LearningMaterial, TimeTableRecord
from organization.models import PlacementDrive, PlacementApplication
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'full_name', 'role', 'last_login', 'is_staff', 'is_active']
    list_filter = UserAdmin.list_filter + ('role',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'full_name')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'full_name')}),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_last_login', 'roll_number', 'department', 'semester', 'placement_eligible']
    search_fields = ['user__username', 'user__full_name', 'roll_number']
    list_filter = ['department', 'semester', 'placement_eligible']

    def get_last_login(self, obj):
        return obj.user.last_login
    get_last_login.short_description = 'Last Login'
    get_last_login.admin_order_field = 'user__last_login'

class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_last_login', 'faculty_uid', 'department', 'designation']
    search_fields = ['user__username', 'user__full_name', 'faculty_uid']
    list_filter = ['department', 'designation']

    def get_last_login(self, obj):
        return obj.user.last_login
    get_last_login.short_description = 'Last Login'
    get_last_login.admin_order_field = 'user__last_login'

class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'role', 'date_of_drive', 'deadline']
    search_fields = ['company_name', 'role']
    list_filter = ['date_of_drive']

class PlacementApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'drive', 'status', 'applied_at']
    search_fields = ['student__username', 'drive__company_name']
    list_filter = ['status', 'applied_at']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Subject)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(FacultyProfile, FacultyProfileAdmin)
admin.site.register(AttendanceRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'semester', 'exam_type', 'marks_obtained', 'max_marks', 'grade_letter', 'grade_point', 'credits', 'updated_at']
    list_filter  = ['semester', 'exam_type', 'grade_letter', 'subject__department']
    search_fields = ['student__username', 'student__full_name', 'subject__name']
    readonly_fields = ['grade_letter', 'grade_point', 'updated_at']
    ordering = ['-updated_at']
    fieldsets = (
        ('Student & Subject', {'fields': ('student', 'subject', 'semester', 'exam_type')}),
        ('Marks', {'fields': ('marks_obtained', 'max_marks', 'credits')}),
        ('Computed (auto)', {'fields': ('grade_letter', 'grade_point', 'updated_at'), 'classes': ('collapse',)}),
    )

admin.site.register(GradeRecord, GradeRecordAdmin)
admin.site.register(Notification)
admin.site.register(LearningMaterial)
admin.site.register(PlacementDrive, PlacementDriveAdmin)
admin.site.register(PlacementApplication, PlacementApplicationAdmin)


@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'request_type', 'leave_from_date', 'leave_to_date', 'status', 'created_at']
    list_filter = ['request_type', 'status', 'created_at']
    search_fields = ['student__username', 'student__full_name', 'message']
    list_editable = ['status']
    ordering = ['-created_at']
    readonly_fields = ['student', 'request_type', 'message', 'leave_from_date', 'leave_to_date', 'created_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'target_role', 'department', 'semester', 'created_at']
    list_filter = ['target_role', 'department', 'semester', 'created_at']
    search_fields = ['title', 'content', 'author__username']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_department', 'category', 'subject', 'status', 'created_at']
    list_filter = ['category', 'status', 'created_at', 'student__student_profile__department']
    search_fields = ['student__username', 'subject', 'message']
    list_editable = ['status']
    ordering = ['-created_at']

    def get_department(self, obj):
        return obj.student.student_profile.department
    get_department.short_description = 'Department'
