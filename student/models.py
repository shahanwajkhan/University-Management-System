from django.db import models
from core.models import CustomUser, Department
from django.db.models.signals import post_save
from django.dispatch import receiver

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    semester = models.IntegerField(default=1)
    fee_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    placement_eligible = models.BooleanField(default=False)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_till = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    class Meta:
        db_table = 'core_studentprofile'

    def __str__(self):
        return f"{self.user.username}'s Profile"

class PaymentRecord(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payment_records')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_comments = models.TextField(blank=True)

    class Meta:
        db_table = 'core_paymentrecord'

    def __str__(self):
        return f"Payment {self.transaction_id} by {self.student.username}"

class StudentRequest(models.Model):
    TYPE_CHOICES = (
        ('Leave', 'Leave Request'),
        ('Bonafide', 'Bonafide Certificate'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='service_requests')
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    leave_from_date = models.DateField(null=True, blank=True)
    leave_to_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_studentrequest'

class Complaint(models.Model):
    CATEGORY_CHOICES = (
        ('Academic', 'Academic'),
        ('Infrastructure', 'Infrastructure'),
        ('Harassment', 'Harassment'),
        ('Others', 'Others'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    )
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    attachment = models.FileField(upload_to='complaints/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_complaint'

@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'Student':
        StudentProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_student_profile(sender, instance, **kwargs):
    if instance.role == 'Student' and hasattr(instance, 'student_profile'):
        instance.student_profile.save()
