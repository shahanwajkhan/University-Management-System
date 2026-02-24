from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import CustomUser, Department, Subject, Announcement, Notification
from student.models import StudentProfile, PaymentRecord, StudentRequest, Complaint
from faculty.models import FacultyProfile, AttendanceRecord, GradeRecord, LearningMaterial, TimeTableRecord
from organization.models import PlacementDrive, PlacementApplication
from django.db.models import Avg, Sum, F, Count, Q
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect

@login_required(login_url='role_selection')
def student_dashboard(request):
    user = request.user
    
    # Check if profile exists
    profile, created = StudentProfile.objects.get_or_create(user=user)
    
    # --- Subject-wise Attendance ---
    subjects = Subject.objects.filter(department=profile.department) # Or based on registrations if implemented
    attendance_data = []
    total_present_global = 0
    total_classes_global = 0
    
    for subject in subjects:
        records = AttendanceRecord.objects.filter(student=user, subject=subject)
        conducted = records.count()
        attended = records.filter(status=True).count()
        percentage = (attended / conducted * 100) if conducted > 0 else 0
        
        total_present_global += attended
        total_classes_global += conducted
        
        attendance_data.append({
            'subject': subject,
            'conducted': conducted,
            'attended': attended,
            'percentage': round(percentage, 1),
            'warning': percentage < 75 and conducted > 0
        })
    
    overall_attendance_percentage = (total_present_global / total_classes_global * 100) if total_classes_global > 0 else 0
    
    # --- Overall Attendance ---
    records = AttendanceRecord.objects.filter(student=user)
    conducted = records.count()
    attended = records.filter(status=True).count()
    overall_attendance = (attended / conducted * 100) if conducted > 0 else 0
    
    # --- CGPA ---
    grade_records = GradeRecord.objects.filter(student=user)
    total_points = sum(r.grade_point * r.credits for r in grade_records)
    total_credits = sum(r.credits for r in grade_records)
    cgpa = float((total_points / total_credits) if total_credits > 0 else 0)
    cgpa_percentage = (cgpa / 10.0) * 100
    
    # --- Placement Status ---
    eligible_drives_count = PlacementDrive.objects.filter(
        deadline__gte=timezone.now(),
        criteria_cgpa__lte=cgpa,
        criteria_attendance__lte=overall_attendance,
        target_departments=profile.department
    ).count()
    
    # --- Recent Requests ---
    recent_requests = StudentRequest.objects.filter(student=user).order_by('-created_at')[:3]
    
    # --- Notifications ---
    notifications = Notification.objects.filter(user=user).order_by('-timestamp')[:5]
    
    # --- Real Announcements (Notice Board) ---
    announcements = Announcement.objects.filter(
        (Q(department=profile.department) | Q(department__isnull=True)),
        (Q(semester=profile.semester) | Q(semester__isnull=True)),
        Q(target_role__in=['Student', 'Both'])
    ).order_by('-created_at')[:5]
    
    # --- Today's Timetable ---
    import datetime, json
    today_name = datetime.datetime.today().strftime('%A')
    today_slots = TimeTableRecord.objects.filter(
        department=profile.department,
        semester=profile.semester,
        day=today_name,
        target_role__in=['Student', 'Both']
    ).select_related('subject').order_by('start_time')
    today_schedule_json = json.dumps([
        {
            'subject': slot.subject.name,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'room': slot.room or '',
        }
        for slot in today_slots
    ])

    context = {
        'profile': profile,
        'attendance_percentage': round(overall_attendance, 2),
        'attendance_data': attendance_data,
        'cgpa': round(cgpa, 2),
        'cgpa_percentage': round(cgpa_percentage, 2),
        'notifications': notifications,
        'announcements': announcements,
        'eligible_drives_count': eligible_drives_count,
        'recent_requests': recent_requests,
        'fee_balance': profile.fee_balance,
        'today_schedule_json': today_schedule_json,
    }
    return render(request, 'student/dashboard.html', context)

@login_required(login_url='role_selection')
def learning_materials(request):
    profile = request.user.student_profile
    subjects = Subject.objects.filter(department=profile.department)
    
    # Get filters
    subject_id = request.GET.get('subject')
    search_query = request.GET.get('search')
    
    materials = LearningMaterial.objects.filter(subject__department=profile.department)
    
    if subject_id:
        materials = materials.filter(subject_id=subject_id)
    
    if search_query:
        materials = materials.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    context = {
        'profile': profile,
        'subjects': subjects,
        'materials': materials,
        'selected_subject': subject_id,
        'search_query': search_query,
    }
    return render(request, 'student/learning_materials.html', context)
@login_required(login_url='role_selection')
def student_results(request):
    user = request.user
    grade_records = GradeRecord.objects.filter(student=user).order_by('semester', 'subject__name')
    
    # Group by semester
    semester_results = {}
    for record in grade_records:
        if record.semester not in semester_results:
            semester_results[record.semester] = []
        semester_results[record.semester].append(record)
    
    # Calculate GPA per semester
    semester_gpas = {}
    total_weighted_points_global = 0.0
    total_credits_global = 0
    
    for sem, records in semester_results.items():
        points = sum(float(r.grade_point) * int(r.credits) for r in records)
        credits = sum(int(r.credits) for r in records)
        gpa = (points / credits) if credits > 0 else 0.0
        semester_gpas[sem] = round(gpa, 2)
        
        total_weighted_points_global += points
        total_credits_global += credits
    
    cgpa = (total_weighted_points_global / total_credits_global) if total_credits_global > 0 else 0.0
    
    grade_scale = [
        ('O',  'Outstanding ≥90%', '#dcfce7', '#15803d'),
        ('A+', 'Excellent ≥80%',   '#d1fae5', '#047857'),
        ('A',  'Very Good ≥70%',   '#dbeafe', '#1d4ed8'),
        ('B+', 'Good ≥60%',        '#ede9fe', '#6d28d9'),
        ('B',  'Above Avg ≥55%',   '#fef3c7', '#b45309'),
        ('C',  'Average ≥50%',     '#ffedd5', '#c2410c'),
        ('P',  'Pass ≥40%',        '#f0fdf4', '#166534'),
        ('F',  'Fail <40%',        '#fee2e2', '#b91c1c'),
    ]
    
    context = {
        'semester_results': semester_results,
        'semester_gpas': semester_gpas,
        'cgpa': round(cgpa, 2),
        'cgpa_pct': round((cgpa / 10.0) * 100, 1),
        'total_subjects': sum(len(r) for r in semester_results.values()),
        'total_credits': int(total_credits_global),
        'grade_scale': grade_scale,
    }
    return render(request, 'student/results.html', context)

@login_required(login_url='role_selection')
def placement_portal(request):
    user = request.user
    profile = user.student_profile
    drives = PlacementDrive.objects.filter(deadline__gte=timezone.now()).order_by('date_of_drive')
    applications = PlacementApplication.objects.filter(student=user)
    applied_drive_ids = applications.values_list('drive_id', flat=True)
    
    # Calculate Attendance
    records = AttendanceRecord.objects.filter(student=user)
    conducted = records.count()
    attended = records.filter(status=True).count()
    overall_attendance = (attended / conducted * 100) if conducted > 0 else 0
    
    # Calculate CGPA
    grade_records = GradeRecord.objects.filter(student=user)
    total_points = sum(r.grade_point * r.credits for r in grade_records)
    total_credits = sum(r.credits for r in grade_records)
    cgpa = (total_points / total_credits) if total_credits > 0 else 0
    
    eligible_drives = []
    ineligible_drives = []
    
    for drive in drives:
        is_eligible = (
            cgpa >= drive.criteria_cgpa and 
            overall_attendance >= drive.criteria_attendance and 
            profile.department in drive.target_departments.all()
        )
        
        # Add 'has_applied' attribute to drive object for template logic
        drive.has_applied = drive.id in applied_drive_ids
        
        if is_eligible:
            eligible_drives.append(drive)
        else:
            ineligible_drives.append(drive)
            
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_cv':
            resume = request.FILES.get('resume')
            if resume:
                profile.resume = resume
                profile.save()
                messages.success(request, "Resume updated successfully!")
            else:
                messages.error(request, "Please select a file to upload.")
            return redirect('placement_portal')

        elif 'drive_id' in request.POST:
            drive_id = request.POST.get('drive_id')
            use_profile_resume = request.POST.get('use_profile_resume') == 'true'
            resume = request.FILES.get('resume')
            
            try:
                drive = PlacementDrive.objects.get(id=drive_id)
                
                # Additional safety check for eligibility and existing application
                is_eligible = (
                    cgpa >= drive.criteria_cgpa and 
                    overall_attendance >= drive.criteria_attendance and 
                    profile.department in drive.target_departments.all()
                )
                
                if not is_eligible:
                    messages.error(request, "You do not meet the eligibility criteria for this drive.")
                elif drive.id in applied_drive_ids:
                    messages.warning(request, "You have already applied for this drive.")
                else:
                    target_resume = None
                    if use_profile_resume and profile.resume:
                        target_resume = profile.resume
                    elif resume:
                        target_resume = resume
                    
                    if target_resume:
                        PlacementApplication.objects.create(
                            drive=drive,
                            student=user,
                            resume=target_resume
                        )
                        messages.success(request, f"Successfully applied for {drive.company_name}!")
                    else:
                        messages.error(request, "Please provide a resume (either from profile or upload).")
                    
            except PlacementDrive.DoesNotExist:
                messages.error(request, "Placement drive not found.")
                
            return redirect('placement_portal')
    
    context = {
        'profile': profile,
        'eligible_drives': eligible_drives,
        'ineligible_drives': ineligible_drives,
        'applications': applications,
        'cgpa': cgpa,
        'attendance': overall_attendance
    }
    return render(request, 'student/placement.html', context)

@login_required(login_url='role_selection')
def fee_portal(request):
    user = request.user
    profile = user.student_profile

    if request.method == 'POST':
        import uuid
        amount = request.POST.get('amount')
        transaction_id = request.POST.get('transaction_id', '').strip() or f"TXN-{uuid.uuid4().hex[:10].upper()}"
        receipt = request.FILES.get('receipt')

        if not amount:
            messages.error(request, "Please enter a valid payment amount.")
            return redirect('fee_portal')

        try:
            from decimal import Decimal
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError
        except (ValueError, Exception):
            messages.error(request, "Invalid amount entered.")
            return redirect('fee_portal')

        if PaymentRecord.objects.filter(transaction_id=transaction_id).exists():
            messages.error(request, "A payment with this Transaction ID already exists. Please use a unique ID.")
            return redirect('fee_portal')

        PaymentRecord.objects.create(
            student=user,
            amount=amount_decimal,
            transaction_id=transaction_id,
            receipt=receipt,
            status='Pending',
        )
        messages.success(request, "Payment submitted successfully! It is now pending admin approval.")
        return redirect('fee_portal')

    payments = PaymentRecord.objects.filter(student=user).order_by('-date')
    total_fee = 120000
    amount_paid = total_fee - float(profile.fee_balance)

    context = {
        'profile': profile,
        'payments': payments,
        'total_fee': total_fee,
        'amount_paid': amount_paid,
    }
    return render(request, 'student/fees.html', context)

@login_required(login_url='role_selection')
def service_requests(request):
    user = request.user
    requests_list = StudentRequest.objects.filter(student=user).order_by('-created_at')
    
    total_count = requests_list.count()
    approved_count = requests_list.filter(status='Approved').count()
    pending_count = requests_list.filter(status='Pending').count()
    
    if request.method == 'POST':
        req_type = request.POST.get('request_type')
        message = request.POST.get('message')
        leave_from_date = request.POST.get('leave_from_date') or None
        leave_to_date = request.POST.get('leave_to_date') or None
        StudentRequest.objects.create(
            student=user,
            request_type=req_type,
            message=message,
            leave_from_date=leave_from_date,
            leave_to_date=leave_to_date,
        )
        messages.success(request, "Request submitted successfully!")
        return redirect('service_requests')
        
    context = {
        'requests': requests_list,
        'total_requests': total_count,
        'approved_requests': approved_count,
        'pending_requests': pending_count
    }
    return render(request, 'student/requests.html', context)

@login_required(login_url='role_selection')
def student_timetable(request):
    user = request.user
    profile = user.student_profile
    
    # Get timetable for student's department and semester
    timetable_records = TimeTableRecord.objects.filter(
        department=profile.department,
        semester=profile.semester,
        target_role__in=['Student', 'Both']
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
    return render(request, 'student/timetable.html', context)

@login_required(login_url='role_selection')
def grievance_portal(request):
    user = request.user
    complaints = Complaint.objects.filter(student=user).order_by('-created_at')
    
    if request.method == 'POST':
        category = request.POST.get('category')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        
        Complaint.objects.create(
            student=user, 
            category=category, 
            subject=subject, 
            message=message, 
            attachment=attachment
        )
        messages.success(request, "Complaint submitted successfully!")
        return redirect('grievance_portal')
        
    context = {'complaints': complaints}
    return render(request, 'student/grievance.html', context)
@login_required(login_url='role_selection')
def academic_advisor_api(request):
    user = request.user
    profile = user.student_profile
    query = request.GET.get('query', '').lower()
    
    # --- Data Collection ---
    records = AttendanceRecord.objects.filter(student=user)
    conducted = records.count()
    attended = records.filter(status=True).count()
    attendance_perc = (attended / conducted * 100) if conducted > 0 else 0
    
    grade_records = GradeRecord.objects.filter(student=user)
    total_points = sum(r.grade_point * r.credits for r in grade_records)
    total_credits = sum(r.credits for r in grade_records)
    cgpa = (total_points / total_credits) if total_credits > 0 else 0
    
    backlogs = grade_records.filter(grade_point__lt=4).count() # Assuming < 4 is a fail/backlog
    
    response_text = ""
    icon = "bi-robot"
    
    # --- Analysis Logic ---
    if "eligible" in query or "semester 5" in query:
        # Simple rule: CGPA > 5.0 and Backlogs < 3
        if cgpa >= 5.0 and backlogs < 3:
            response_text = f"Based on your current CGPA of **{round(cgpa, 2)}** and only **{backlogs}** backlogs, you are **ELIGIBLE** for Semester 5. Keep maintaining this momentum!"
        else:
            reasons = []
            if cgpa < 5.0: reasons.append(f"CGPA is below 5.0 (Current: {round(cgpa, 2)})")
            if backlogs >= 3: reasons.append(f"Backlogs exceed the limit (Current: {backlogs})")
            response_text = f"Currently, you are **NOT FULLY ELIGIBLE**. Issues: {', '.join(reasons)}. I recommend focusing on clearing backlogs immediately."
            
    elif "cgpa" in query or "improve" in query:
        low_subjects = grade_records.filter(grade_point__lt=7).order_by('grade_point')[:2]
        if low_subjects:
            subjects_str = ", ".join([s.subject.name for s in low_subjects])
            response_text = f"To boost your CGPA, focus on subjects like **{subjects_str}** where your grade point is lower. Scoring an 8.0+ in next semester's core subjects could raise your CGPA by approximately 0.2-0.4 points."
        else:
            response_text = "Your CGPA is already excellent! To maintain or reach a 9.0+, focus on high-credit elective subjects and ensure consistent internal assessment marks."
            
    elif "attendance" in query or "75%" in query:
        if attendance_perc >= 75:
            # How many classes can they miss?
            can_miss = (attended / 0.75) - conducted if conducted > 0 else 0
            response_text = f"You are in the **Green Zone** at **{round(attendance_perc, 1)}%**. You can technically miss about **{int(can_miss)}** more lectures while staying above 75%. But don't make it a habit!"
        else:
            # How many classes to attend?
            needed = (0.75 * conducted - attended) / (1 - 0.75) if conducted > 0 else 0
            response_text = f"Warning! You are at **{round(attendance_perc, 1)}%**. You need to attend the next **{max(1, int(needed))}** consecutive lectures to cross the 75% safety threshold."
            icon = "bi-exclamation-triangle-fill"
            
    else:
        response_text = f"Hello {user.username}! I am your AI Academic Advisor. I can analyze your **Eligibility**, **CGPA strategies**, or **Attendance projections**. Try asking one of the quick questions below!"

    return JsonResponse({
        'status': 'success',
        'response': response_text,
        'icon': icon,
        'metrics': {
            'cgpa': round(cgpa, 2),
            'attendance': round(attendance_perc, 1),
            'backlogs': backlogs
        }
    })

@login_required(login_url='role_selection')
def student_profile(request):
    if request.user.role != 'Student':
        return redirect('home')
        
    profile = request.user.student_profile
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        profile_picture = request.FILES.get('profile_picture')
        
        if roll_number:
            profile.roll_number = roll_number
        if profile_picture:
            profile.profile_picture = profile_picture
            
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_profile')
        
    context = {
        'profile': profile
    }
    return render(request, 'student/profile.html', context)

@login_required(login_url='role_selection')
def download_id_card(request):
    if request.user.role != 'Student':
        return redirect('home')
        
    profile = request.user.student_profile
    context = {
        'profile': profile,
        'user': request.user
    }
    return render(request, 'student/id_card.html', context)
