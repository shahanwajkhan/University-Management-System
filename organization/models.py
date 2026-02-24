from django.db import models
from core.models import CustomUser, Department

class PlacementDrive(models.Model):
    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    description = models.TextField()
    package = models.CharField(max_length=100)
    criteria_cgpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    criteria_attendance = models.IntegerField(default=0, help_text="Minimum attendance percentage required")
    target_departments = models.ManyToManyField(Department)
    date_of_drive = models.DateField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=(('Open', 'Open'), ('Closed', 'Closed')), default='Open')

    class Meta:
        db_table = 'core_placementdrive'

    def __str__(self):
        return f"{self.company_name} - {self.role}"

class PlacementApplication(models.Model):
    STATUS_CHOICES = (
        ('Applied', 'Applied'),
        ('Shortlisted', 'Shortlisted'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
    )
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='placement_applications')
    resume = models.FileField(upload_to='resumes/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_placementapplication'

