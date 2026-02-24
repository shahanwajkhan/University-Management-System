from django.db import models
from core.models import CustomUser, Department, Subject
from django.db.models.signals import post_save
from django.dispatch import receiver

class FacultyProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='faculty_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    faculty_uid = models.CharField(max_length=20, unique=True, null=True, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    assigned_subjects = models.ManyToManyField(Subject, related_name='assigned_faculty', blank=True)
    joining_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    class Meta:
        db_table = 'core_facultyprofile'

    def __str__(self):
        return f"{self.user.username}'s Faculty Profile"

class AttendanceRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance_records', null=True)
    date = models.DateField()
    status = models.BooleanField(default=True) # True for Present, False for Absent
    
    class Meta:
        unique_together = ('student', 'subject', 'date')
        db_table = 'core_attendancerecord'

class GradeRecord(models.Model):
    EXAM_TYPE_CHOICES = (
        ('Internal', 'Internal Exam'),
        ('External', 'External Exam'),
        ('Final', 'Final Exam'),
        ('Practical', 'Practical'),
    )
    GRADE_CHOICES = (
        ('O',  'Outstanding (O)'),
        ('A+', 'Excellent (A+)'),
        ('A',  'Very Good (A)'),
        ('B+', 'Good (B+)'),
        ('B',  'Above Average (B)'),
        ('C',  'Average (C)'),
        ('P',  'Pass (P)'),
        ('F',  'Fail (F)'),
    )
    student    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grade_records')
    subject    = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grade_records', null=True)
    semester   = models.IntegerField(default=1)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_marks  = models.IntegerField(default=100)
    exam_type  = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default='Final')
    grade_letter = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    grade_point  = models.DecimalField(max_digits=4, decimal_places=2, default=0)  # auto-computed
    credits    = models.IntegerField(default=3)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_graderecord'

    def _compute_grade(self):
        """Compute grade_letter and grade_point from marks percentage."""
        try:
            marks = float(self.marks_obtained or 0)
            max_m = int(self.max_marks or 100)
        except (ValueError, TypeError):
            return 'F', 0.0
        if max_m <= 0:
            return 'F', 0.0
        pct = marks / max_m * 100
        if pct >= 90:   return 'O',  10.0
        elif pct >= 80: return 'A+',  9.0
        elif pct >= 70: return 'A',   8.0
        elif pct >= 60: return 'B+',  7.0
        elif pct >= 55: return 'B',   6.0
        elif pct >= 50: return 'C',   5.0
        elif pct >= 40: return 'P',   4.0
        else:           return 'F',   0.0

    def save(self, *args, **kwargs):
        grade, gp = self._compute_grade()
        self.grade_letter = grade
        self.grade_point  = round(gp, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} - {self.subject.name if self.subject else 'N/A'}: {self.grade_letter} ({self.marks_obtained}/{self.max_marks})"

class LearningMaterial(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='materials/')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='materials')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_materials')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_learningmaterial'

    def __str__(self):
        return f"{self.title} ({self.subject.code})"

class TimeTableRecord(models.Model):
    DAY_CHOICES = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    )
    TARGET_ROLE_CHOICES = (
        ('Student', 'Student'),
        ('Faculty', 'Faculty'),
        ('Both', 'Both'),
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='timetable')
    semester = models.IntegerField(default=1)
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable')
    faculty = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='timetable_classes', limit_choices_to={'role': 'Faculty'})
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    target_role = models.CharField(max_length=20, choices=TARGET_ROLE_CHOICES, default='Both')

    class Meta:
        ordering = ['day', 'start_time']
        db_table = 'core_timetablerecord'

    def __str__(self):
        return f"{self.day} - {self.subject.name} ({self.start_time})"

@receiver(post_save, sender=CustomUser)
def create_faculty_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'Faculty':
        FacultyProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_faculty_profile(sender, instance, **kwargs):
    if instance.role == 'Faculty' and hasattr(instance, 'faculty_profile'):
        instance.faculty_profile.save()
