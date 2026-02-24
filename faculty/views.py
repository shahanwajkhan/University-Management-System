from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.urls import reverse
from core.models import CustomUser, Department, Subject, Announcement, Notification
from student.models import StudentProfile, PaymentRecord, StudentRequest, Complaint
from faculty.models import FacultyProfile, AttendanceRecord, GradeRecord, LearningMaterial, TimeTableRecord
from organization.models import PlacementDrive, PlacementApplication
from django.contrib import messages
from datetime import date, datetime, timedelta
from django.http import HttpResponse
from io import BytesIO

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

@login_required(login_url='role_selection')
def faculty_dashboard(request):
    if request.user.role != 'Faculty':
        return redirect('home')
    
    profile, created = FacultyProfile.objects.get_or_create(user=request.user)
    subjects = _faculty_subjects_for_attendance(profile)
    uploaded_materials = LearningMaterial.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    
    # Get today's day name (Monday, Tuesday, etc.)
    today = date.today()
    day_name = today.strftime('%A')
    
    # Total Classes Today - count timetable records for today's day
    total_classes_today = TimeTableRecord.objects.filter(
        faculty=request.user,
        day=day_name
    ).count()
    
    # Pending Complaints - complaints from students in faculty's department
    pending_complaints = 0
    if profile.department:
        pending_complaints = Complaint.objects.filter(
            student__student_profile__department=profile.department,
            status='Pending'
        ).count()
    
    # Attendance Summary - calculate statistics for faculty's subjects
    attendance_summary = {}
    if subjects.exists():
        # Get all attendance records for faculty's subjects
        attendance_records = AttendanceRecord.objects.filter(
            subject__in=subjects
        )
        
        # Calculate total students across all subjects
        total_students = StudentProfile.objects.filter(
            department__in=subjects.values_list('department', flat=True).distinct()
        ).count()
        
        # Calculate present and absent counts
        present_count = attendance_records.filter(status=True).count()
        absent_count = attendance_records.filter(status=False).count()
        total_records = attendance_records.count()
        
        # Calculate average attendance percentage
        if total_records > 0:
            attendance_percentage = (present_count / total_records) * 100
        else:
            attendance_percentage = 0
        
        attendance_summary = {
            'total_students': total_students,
            'present_count': present_count,
            'absent_count': absent_count,
            'total_records': total_records,
            'attendance_percentage': round(attendance_percentage, 1)
        }
    else:
        attendance_summary = {
            'total_students': 0,
            'present_count': 0,
            'absent_count': 0,
            'total_records': 0,
            'attendance_percentage': 0
        }
    
    # Announcements for Faculty Notice Board
    from django.db.models import Q
    announcements = Announcement.objects.filter(
        (Q(department=profile.department) | Q(department__isnull=True)),
        Q(target_role__in=['Faculty', 'Both'])
    ).order_by('-created_at')[:5]

    # Today's schedule JSON for dashboard timetable widget
    import json
    today_slots = TimeTableRecord.objects.filter(
        faculty=request.user,
        day=day_name
    ).select_related('subject').order_by('start_time')
    today_schedule_json = json.dumps([
        {
            'subject': slot.subject.name,
            'code':    slot.subject.code,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time':   slot.end_time.strftime('%H:%M'),
            'room': slot.room or 'TBD',
        }
        for slot in today_slots
    ])

    context = {
        'profile': profile,
        'subjects': subjects,
        'subjects_count': subjects.count(),
        'uploaded_materials': uploaded_materials,
        'faculty_name': request.user.full_name or request.user.username,
        'department': profile.department.name if profile.department else 'Not Assigned',
        'total_classes_today': total_classes_today,
        'pending_complaints': pending_complaints,
        'attendance_summary': attendance_summary,
        'announcements': announcements,
        'today_schedule_json': today_schedule_json,
        'today_day': day_name,
    }
    return render(request, 'faculty/dashboard.html', context)

@login_required(login_url='role_selection')
def mark_attendance(request, subject_id):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    subject = get_object_or_404(Subject, id=subject_id)
    profile = request.user.faculty_profile
    if not _faculty_can_access_subject(profile, subject):
        messages.error(request, "You do not have access to mark attendance for this subject.")
        return redirect('faculty_dashboard')
    
    # Get all students in the department of this subject
    students = StudentProfile.objects.filter(department=subject.department).order_by('roll_number')
    
    # Get selected date from request
    selected_date = request.GET.get('date', date.today().isoformat())
    try:
        attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        attendance_date = date.today()
    
    if request.method == 'POST':
        attendance_date = request.POST.get('date', date.today().isoformat())
        try:
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except:
            attendance_date = date.today()
            
        for student_profile in students:
            status = request.POST.get(f'status_{student_profile.user.id}') == 'present'
            AttendanceRecord.objects.update_or_create(
                student=student_profile.user,
                subject=subject,
                date=attendance_date,
                defaults={'status': status}
            )
        messages.success(request, f"Attendance for {subject.name} on {attendance_date} saved successfully!")
        return redirect('mark_attendance', subject_id=subject_id)
        
    # Load existing attendance records for the selected date
    existing_records = {}
    if attendance_date:
        records = AttendanceRecord.objects.filter(
            subject=subject,
            date=attendance_date
        )
        for record in records:
            existing_records[record.student.id] = record.status
    
    # Prepare student data with attendance status
    students_with_attendance = []
    for student_profile in students:
        students_with_attendance.append({
            'profile': student_profile,
            'existing_status': existing_records.get(student_profile.user.id, None)
        })
    
    context = {
        'subject': subject,
        'students': students,
        'students_with_attendance': students_with_attendance,
        'today': date.today().isoformat(),
        'selected_date': attendance_date.isoformat(),
        'existing_records': existing_records,
    }
    return render(request, 'faculty/mark_attendance.html', context)

def _faculty_subjects_for_attendance(profile):
    """
    Returns all subjects available for faculty attendance management.
    Shows subjects across all departments so faculty can mark attendance
    for any subject (access control is enforced separately).
    Assigned subjects for the faculty's department appear first.
    """
    from django.db.models import Case, When, BooleanField

    # Always show ALL subjects, but put the faculty's dept subjects first
    if profile.department:
        return Subject.objects.all().order_by(
            Case(
                When(department=profile.department, then=0),
                default=1,
            ),
            'department__name',
            'code',
        )

    # No dept at all — show everything
    return Subject.objects.all().select_related('department').order_by('department__name', 'code')


def _faculty_can_access_subject(profile, subject):
    """True if faculty can mark/view/export attendance for this subject.
    Since the subject picker shows all subjects, we allow access to all."""
    return True


def edit_attendance(request):
    """Select subject and date to edit attendance"""
    if request.user.role != 'Faculty':
        return redirect('home')
    
    profile = request.user.faculty_profile
    subjects = _faculty_subjects_for_attendance(profile)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        attendance_date = request.POST.get('date')
        
        if subject_id and attendance_date:
            url = reverse('mark_attendance', args=[subject_id]) + f'?date={attendance_date}'
            return redirect(url)
        else:
            messages.error(request, "Please select both subject and date.")
    
    context = {
        'subjects': subjects,
        'today': date.today().isoformat(),
    }
    return render(request, 'faculty/edit_attendance.html', context)

@login_required(login_url='role_selection')
def view_attendance_percentage(request, subject_id):
    """View attendance percentage of all students for a subject"""
    if request.user.role != 'Faculty':
        return redirect('home')
    
    subject = get_object_or_404(Subject, id=subject_id)
    profile = request.user.faculty_profile
    if not _faculty_can_access_subject(profile, subject):
        messages.error(request, "You do not have access to this subject.")
        return redirect('faculty_dashboard')
    
    # Get all students in the department
    students = StudentProfile.objects.filter(department=subject.department).order_by('roll_number')
    
    # Calculate attendance percentage for each student
    attendance_data = []
    good_count = 0
    low_count = 0
    
    for student_profile in students:
        records = AttendanceRecord.objects.filter(
            student=student_profile.user,
            subject=subject
        )
        total_classes = records.count()
        present_classes = records.filter(status=True).count()
        
        if total_classes > 0:
            percentage = (present_classes / total_classes) * 100
        else:
            percentage = 0
        
        status = 'Good' if percentage >= 75 else 'Low'
        if status == 'Good':
            good_count += 1
        else:
            low_count += 1
        
        attendance_data.append({
            'student': student_profile,
            'total_classes': total_classes,
            'present_classes': present_classes,
            'absent_classes': total_classes - present_classes,
            'percentage': round(percentage, 2),
            'status': status
        })
    
    context = {
        'subject': subject,
        'attendance_data': attendance_data,
        'total_students': len(attendance_data),
        'good_count': good_count,
        'low_count': low_count,
    }
    return render(request, 'faculty/view_attendance_percentage.html', context)

@login_required(login_url='role_selection')
def export_attendance_pdf(request, subject_id):
    """Export attendance report as PDF"""
    if request.user.role != 'Faculty':
        return redirect('home')
    
    if not REPORTLAB_AVAILABLE:
        messages.error(request, "PDF generation library (reportlab) is not installed. Please install it using: pip install reportlab")
        return redirect('view_attendance_percentage', subject_id=subject_id)
    
    subject = get_object_or_404(Subject, id=subject_id)
    profile = request.user.faculty_profile
    if not _faculty_can_access_subject(profile, subject):
        messages.error(request, "You do not have access to this subject.")
        return redirect('faculty_dashboard')
    
    # Get date range from request
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)  # Default: last 30 days
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = date.today()
    except:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    # Get all students
    students = StudentProfile.objects.filter(department=subject.department).order_by('roll_number')
    
    # Get attendance records
    attendance_records = AttendanceRecord.objects.filter(
        subject=subject,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date', 'student')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#ff5722'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Title
    title = Paragraph(f"Attendance Report - {subject.name}", title_style)
    elements.append(title)
    
    # Subject info
    info_text = f"<b>Subject Code:</b> {subject.code}<br/>"
    info_text += f"<b>Department:</b> {subject.department.name}<br/>"
    info_text += f"<b>Date Range:</b> {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}<br/>"
    info_text += f"<b>Generated On:</b> {date.today().strftime('%B %d, %Y')}"
    info = Paragraph(info_text, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 0.3*inch))
    
    # Prepare table data
    table_data = [['Roll No.', 'Student Name', 'Total Classes', 'Present', 'Absent', 'Percentage', 'Status']]
    
    for student_profile in students:
        student_records = attendance_records.filter(student=student_profile.user)
        total_classes = student_records.count()
        present_classes = student_records.filter(status=True).count()
        absent_classes = total_classes - present_classes
        
        if total_classes > 0:
            percentage = (present_classes / total_classes) * 100
        else:
            percentage = 0
        
        status = 'Good' if percentage >= 75 else 'Low'
        
        table_data.append([
            student_profile.roll_number or 'N/A',
            student_profile.user.full_name or student_profile.user.username,
            str(total_classes),
            str(present_classes),
            str(absent_classes),
            f"{percentage:.2f}%",
            status
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff5722')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Create response
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f'attendance_report_{subject.code}_{start_date}_{end_date}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required(login_url='role_selection')
def upload_material(request):
    if request.user.role != 'Faculty':
        return redirect('home')
    
    profile = request.user.faculty_profile
    subjects = _faculty_subjects_for_attendance(profile)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        uploaded_file = request.FILES.get('file')
        
        if uploaded_file and subject_id:
            subject = get_object_or_404(Subject, id=subject_id)
            LearningMaterial.objects.create(
                title=title,
                description=description,
                file=uploaded_file,
                subject=subject,
                uploaded_by=request.user
            )
            messages.success(request, f"Material '{title}' uploaded successfully!")
            return redirect('upload_material')
        else:
            messages.error(request, "Please provide both a file and a subject.")
            
    materials = LearningMaterial.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
            
    context = {
        'subjects': subjects,
        'materials': materials,
    }
    return render(request, 'faculty/upload_material.html', context)

@login_required(login_url='role_selection')
def edit_material(request, material_id):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    material = get_object_or_404(LearningMaterial, id=material_id, uploaded_by=request.user)
    profile = request.user.faculty_profile
    subjects = _faculty_subjects_for_attendance(profile)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        uploaded_file = request.FILES.get('file')
        
        if title and subject_id:
            subject = get_object_or_404(Subject, id=subject_id)
            material.title = title
            material.description = description
            material.subject = subject
            
            if uploaded_file:
                material.file = uploaded_file
                
            material.save()
            messages.success(request, f"Material '{title}' updated successfully!")
            return redirect('upload_material')
        else:
            messages.error(request, "Please provide a valid title and subject.")
            
    context = {
        'material': material,
        'subjects': subjects,
    }
    return render(request, 'faculty/edit_material.html', context)

@login_required(login_url='role_selection')
def delete_material(request, material_id):
    material = get_object_or_404(LearningMaterial, id=material_id, uploaded_by=request.user)
    title = material.title
    material.delete()
    messages.success(request, f"Material '{title}' deleted.")
    return redirect('upload_material')

@login_required(login_url='role_selection')
def faculty_timetable(request):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    profile = request.user.faculty_profile
    
    # Get timetable for this faculty member
    timetable_records = TimeTableRecord.objects.filter(
        faculty=request.user,
        target_role__in=['Faculty', 'Both']
    ).order_by('day', 'start_time')
    
    # Group by day
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    schedule = {day: [] for day in days}
    for record in timetable_records:
        schedule[record.day].append(record)
        
    # Isolate Today's schedule
    import datetime
    today = datetime.datetime.today().strftime('%A')
    today_schedule = schedule.get(today, [])
    
    context = {
        'profile': profile,
        'schedule': schedule,
        'days': days,
        'today': today,
        'today_schedule': today_schedule,
    }
    return render(request, 'faculty/timetable.html', context)

@login_required(login_url='role_selection')
def faculty_profile(request):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    profile = request.user.faculty_profile
    if request.method == 'POST':
        designation = request.POST.get('designation')
        faculty_uid = request.POST.get('faculty_uid')
        profile_picture = request.FILES.get('profile_picture')
        
        if designation:
            profile.designation = designation
        if faculty_uid:
            profile.faculty_uid = faculty_uid
        if profile_picture:
            profile.profile_picture = profile_picture
            
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('faculty_profile')
        
    context = {
        'profile': profile
    }
    return render(request, 'faculty/profile.html', context)

@login_required(login_url='role_selection')
def download_faculty_id_card(request):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    profile = request.user.faculty_profile
    context = {
        'profile': profile,
        'user': request.user
    }
    return render(request, 'faculty/id_card.html', context)

@login_required(login_url='role_selection')
def manage_announcements(request):
    if request.user.role != 'Faculty':
        return redirect('home')
    
    profile = request.user.faculty_profile
    departments = Department.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        dept_id = request.POST.get('department')
        semester = request.POST.get('semester')
        target_role = request.POST.get('target_role', 'Student')
        
        if title and content:
            dept = None
            if dept_id:
                dept = get_object_or_404(Department, id=dept_id)
            
            sem_val = None
            if semester:
                try:
                    sem_val = int(semester)
                except ValueError:
                    sem_val = None
                    
            Announcement.objects.create(
                author=request.user,
                title=title,
                content=content,
                department=dept,
                semester=sem_val,
                target_role=target_role
            )
            messages.success(request, 'Announcement created successfully!')
            return redirect('faculty_announcements')

    # Show faculty's own announcements + admin-posted ones targeting faculty/this dept
    from django.db.models import Q
    own_announcements = Announcement.objects.filter(author=request.user)
    admin_announcements = Announcement.objects.filter(
        Q(target_role__in=['Faculty', 'Both']) &
        (Q(department=profile.department) | Q(department__isnull=True))
    ).exclude(author=request.user)
    
    from itertools import chain
    from operator import attrgetter
    announcements = sorted(
        chain(own_announcements, admin_announcements),
        key=attrgetter('created_at'), reverse=True
    )

    context = {
        'announcements': announcements,
        'departments': departments,
    }
    return render(request, 'faculty/announcements.html', context)

@login_required(login_url='role_selection')
def delete_announcement(request, announcement_id):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    announcement = get_object_or_404(Announcement, id=announcement_id, author=request.user)
    announcement.delete()
    messages.success(request, 'Announcement deleted successfully!')
    return redirect('faculty_announcements')

@login_required(login_url='role_selection')
def manage_complaints(request):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    profile = request.user.faculty_profile
    # Show Academic complaints — filter by dept if faculty has one, else show all
    if profile.department:
        complaints = Complaint.objects.filter(
            category='Academic',
            student__student_profile__department=profile.department
        ).order_by('-created_at')
    else:
        complaints = Complaint.objects.filter(category='Academic').order_by('-created_at')

    context = {
        'complaints': complaints,
        'profile': profile
    }
    return render(request, 'faculty/complaints.html', context)

@login_required(login_url='role_selection')
def update_complaint(request, complaint_id):
    if request.user.role != 'Faculty':
        return redirect('home')
        
    profile = request.user.faculty_profile
    complaint = get_object_or_404(Complaint, id=complaint_id, student__student_profile__department=profile.department)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks')
        
        if status:
            complaint.status = status
        if remarks:
            complaint.admin_comments = remarks
            
        complaint.save()
        messages.success(request, "Complaint updated successfully!")
        return redirect('faculty_complaints')
        
    return redirect('faculty_complaints')
