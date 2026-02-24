from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.urls import reverse
from core.models import CustomUser, Department, Subject, Announcement, Notification
from student.models import StudentProfile, PaymentRecord, StudentRequest, Complaint
from faculty.models import FacultyProfile, AttendanceRecord, GradeRecord, LearningMaterial, TimeTableRecord
from organization.models import PlacementDrive, PlacementApplication

@login_required(login_url='role_selection')
def admin_dashboard(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    # Attendance Calculation
    total_attendance = AttendanceRecord.objects.count()
    present_attendance = AttendanceRecord.objects.filter(status=True).count()
    attendance_percentage = (present_attendance / total_attendance * 100) if total_attendance > 0 else 0

    # Fee Collection Summary
    total_collected = PaymentRecord.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = StudentProfile.objects.aggregate(total=Sum('fee_balance'))['total'] or 0

    # Complaint Summary
    complaint_counts = Complaint.objects.values('status').annotate(count=Count('status'))
    complaint_summary = {item['status']: item['count'] for item in complaint_counts}
    
    stats = {
        'total_students': CustomUser.objects.filter(role='Student').count(),
        'total_faculty': CustomUser.objects.filter(role='Faculty').count(),
        'total_departments': Department.objects.count(),
        'total_courses': Subject.objects.count(),
        'active_placements': PlacementDrive.objects.filter(status='Open').count(),
        'attendance_percentage': round(attendance_percentage, 1),
        'pending_complaints': complaint_summary.get('Pending', 0),
        'total_collected': total_collected,
        'total_pending': total_pending,
        'pending_requests_count': StudentRequest.objects.filter(status='Pending').count(),
        'pending_fees_count': PaymentRecord.objects.filter(status='Pending').count(),
    }
    
    recent_complaints = Complaint.objects.order_by('-created_at')[:5]
    recent_announcements = Announcement.objects.filter(author=request.user).order_by('-created_at')[:5]

    # Build real activity log entries for the terminal
    recent_activities = []
    pending_fees = stats['pending_fees_count']
    if pending_fees > 0:
        recent_activities.append({'tag': 'ALERT', 'color': 'warning', 'msg': f'FEE_MODULE: {pending_fees} payment(s) awaiting admin approval', 'link': 'manage_fees'})
    else:
        recent_activities.append({'tag': 'OK', 'color': 'success', 'msg': 'FEE_MODULE: All payments processed. No pending approvals.', 'link': ''})

    pending_req = stats['pending_requests_count']
    if pending_req > 0:
        recent_activities.append({'tag': 'ALERT', 'color': 'warning', 'msg': f'REQUESTS: {pending_req} student request(s) pending review', 'link': 'manage_requests'})
    else:
        recent_activities.append({'tag': 'OK', 'color': 'success', 'msg': 'REQUESTS: No pending student requests.', 'link': ''})

    pending_comp = complaint_summary.get('Pending', 0)
    if pending_comp > 0:
        recent_activities.append({'tag': 'INFO', 'color': 'info', 'msg': f'GRIEVANCE: {pending_comp} unresolved complaint(s) in queue', 'link': 'manage_complaints'})

    open_placements = stats['active_placements']
    if open_placements > 0:
        recent_activities.append({'tag': 'INFO', 'color': 'info', 'msg': f'PLACEMENT: {open_placements} active drive(s) currently live', 'link': 'manage_placements'})

    recent_activities.append({'tag': 'SYS', 'color': 'success', 'msg': f'DB_SYNC: {stats["total_students"]} student & {stats["total_faculty"]} faculty records indexed', 'link': ''})
    recent_activities.append({'tag': 'AUTH', 'color': 'success', 'msg': f'Session started — {request.user.username}', 'link': ''})

    # Mock data for charts (to be replaced with real aggregation if needed)
    attendance_trends = [78, 82, 75, 88, 81, 90, 85] # Last 7 days
    fee_collection_data = [total_collected, total_pending]
    
    context = {
        'stats': stats,
        'complaint_summary': complaint_summary,
        'recent_complaints': recent_complaints,
        'recent_announcements': recent_announcements,
        'admin_name': request.user.full_name or request.user.username,
        'attendance_trends': attendance_trends,
        'fee_collection_data': fee_collection_data,
        'recent_activities': recent_activities,
        'notifications': Notification.objects.filter(user=request.user).order_by('-timestamp')[:5],
    }
    return render(request, 'organization/dashboard.html', context)

@login_required(login_url='role_selection')
def manage_timetable(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    departments = Department.objects.all()
    selected_dept_id = request.GET.get('department')
    selected_semester = request.GET.get('semester', 1)
    
    current_dept = None
    timetable_records = []
    
    if selected_dept_id:
        current_dept = get_object_or_404(Department, id=selected_dept_id)
        timetable_records = TimeTableRecord.objects.filter(
            department=current_dept, 
            semester=selected_semester
        )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            # Handle bulk save or single record update
            record_id = request.POST.get('record_id')
            dept_id = request.POST.get('dept_id')
            semester = request.POST.get('semester')
            day = request.POST.get('day')
            subject_id = request.POST.get('subject_id')
            faculty_id = request.POST.get('faculty_id')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            room = request.POST.get('room')
            target_role = request.POST.get('target_role', 'Both')
            
            # Basic validation
            if start_time >= end_time:
                messages.error(request, "End time must be after start time.")
                return redirect(f"{request.path}?department={dept_id}&semester={semester}")

            if record_id:
                record = get_object_or_404(TimeTableRecord, id=record_id)
            else:
                record = TimeTableRecord()
                
            record.department = get_object_or_404(Department, id=dept_id)
            record.semester = semester
            record.day = day
            record.subject = get_object_or_404(Subject, id=subject_id)
            record.faculty = get_object_or_404(CustomUser, id=faculty_id, role='Faculty')
            record.start_time = start_time
            record.end_time = end_time
            record.room = room
            record.target_role = target_role
            record.save()
            messages.success(request, f"Schedule for {record.subject.name} saved successfully!")
            return redirect(f"{request.path}?department={dept_id}&semester={semester}")

        elif action == 'delete':
            record_id = request.POST.get('record_id')
            record = TimeTableRecord.objects.filter(id=record_id).first()
            if record:
                subj_name = record.subject.name
                record.delete()
                messages.success(request, f"Deleted slot for {subj_name}.")
            return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))

    subjects = Subject.objects.all().order_by('name')
    if current_dept:
        # Also provide filtered subjects if needed, but for the modal let's show all
        # or prioritze the current department's subjects
        subjects = Subject.objects.filter(department=current_dept).order_by('name')
        if not subjects.exists():
             subjects = Subject.objects.all().order_by('name')
             
    faculties = CustomUser.objects.filter(role='Faculty').order_by('username')
    
    context = {
        'departments': departments,
        'selected_dept': current_dept,
        'selected_semester': int(selected_semester),
        'timetable': timetable_records,
        'subjects': subjects,
        'faculties': faculties,
        'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    }
    return render(request, 'organization/manage_timetable.html', context)

@login_required(login_url='role_selection')
def manage_placements(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            drive_id = request.POST.get('drive_id')
            company_name = request.POST.get('company_name')
            role = request.POST.get('role')
            package = request.POST.get('package')
            date_of_drive = request.POST.get('date_of_drive')
            deadline = request.POST.get('deadline')
            criteria_cgpa = request.POST.get('criteria_cgpa')
            status = request.POST.get('status', 'Open')
            
            if drive_id:
                drive = get_object_or_404(PlacementDrive, id=drive_id)
            else:
                drive = PlacementDrive()
            
            drive.company_name = company_name
            drive.role = role
            drive.package = package
            drive.date_of_drive = date_of_drive
            drive.deadline = deadline
            drive.criteria_cgpa = criteria_cgpa
            drive.status = status
            drive.save()
            
            # Update target departments
            dept_ids = request.POST.getlist('departments')
            drive.target_departments.set(Department.objects.filter(id__in=dept_ids))
            
            return redirect('manage_placements')
            
        elif action == 'delete':
            drive_id = request.POST.get('drive_id')
            PlacementDrive.objects.filter(id=drive_id).delete()
            return redirect('manage_placements')

    drives = PlacementDrive.objects.all().order_by('-date_of_drive')
    departments = Department.objects.all()
    context = {
        'drives': drives,
        'departments': departments,
    }
    return render(request, 'organization/manage_placements.html', context)

@login_required(login_url='role_selection')
def manage_departments(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        name = request.POST.get('name')
        dept_id = request.POST.get('dept_id')
        
        if action == 'add':
            if name:
                Department.objects.get_or_create(name=name)
        elif action == 'edit':
            if dept_id and name:
                dept = get_object_or_404(Department, id=dept_id)
                dept.name = name
                dept.save()
        elif action == 'delete':
            if dept_id:
                Department.objects.filter(id=dept_id).delete()
        
        return redirect('manage_departments')

    departments = Department.objects.all().order_by('name')
    context = {
        'departments': departments,
    }
    return render(request, 'organization/manage_departments.html', context)

@login_required(login_url='role_selection')
def manage_subjects(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        name = request.POST.get('name')
        code = request.POST.get('code')
        dept_id = request.POST.get('dept_id')
        subject_id = request.POST.get('subject_id')
        faculty_ids = request.POST.getlist('faculty_ids')
        
        if action == 'add':
            if name and code and dept_id:
                dept = get_object_or_404(Department, id=dept_id)
                subject, created = Subject.objects.get_or_create(
                    code=code, 
                    defaults={'name': name, 'department': dept}
                )
                if not created:
                    subject.name = name
                    subject.department = dept
                    subject.save()
                
                if faculty_ids:
                    all_faculty_profiles = FacultyProfile.objects.all()
                    for fp in all_faculty_profiles:
                        if str(fp.user.id) in faculty_ids:
                            fp.assigned_subjects.add(subject)
                        else:
                            fp.assigned_subjects.remove(subject)
                            
        elif action == 'edit':
            if subject_id and name and code and dept_id:
                subject = get_object_or_404(Subject, id=subject_id)
                subject.name = name
                subject.code = code
                subject.department = get_object_or_404(Department, id=dept_id)
                subject.save()
                
                all_faculty_profiles = FacultyProfile.objects.all()
                for fp in all_faculty_profiles:
                    if str(fp.user.id) in faculty_ids:
                        fp.assigned_subjects.add(subject)
                    else:
                        fp.assigned_subjects.remove(subject)
                        
        elif action == 'delete':
            if subject_id:
                Subject.objects.filter(id=subject_id).delete()
        
        return redirect('manage_subjects')

    subjects = Subject.objects.all().select_related('department').order_by('department__name', 'name')
    departments = Department.objects.all().order_by('name')
    faculties = CustomUser.objects.filter(role='Faculty').select_related('faculty_profile')
    
    context = {
        'subjects': subjects,
        'departments': departments,
        'faculties': faculties,
    }
    return render(request, 'organization/manage_subjects.html', context)

@login_required(login_url='role_selection')
def manage_students(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        roll_number = request.POST.get('roll_number')
        dept_id = request.POST.get('dept_id')
        semester = request.POST.get('semester')
        student_id = request.POST.get('student_id')
        new_password = request.POST.get('new_password')
        
        if action == 'add':
            if username and email and roll_number:
                if StudentProfile.objects.filter(roll_number=roll_number).exists():
                    messages.error(request, f"A student with roll number '{roll_number}' already exists.")
                elif CustomUser.objects.filter(username=username).exists():
                    messages.error(request, f"A user with username '{username}' already exists.")
                elif CustomUser.objects.filter(email=email).exists():
                    messages.error(request, f"A user with email '{email}' already exists.")
                else:
                    try:
                        # Create User
                        user = CustomUser.objects.create_user(
                            username=username,
                            email=email,
                            password='student123', # Default password
                            role='Student',
                            full_name=full_name
                        )
                        # Profile is created by signal, just update it
                        profile = user.student_profile
                        profile.roll_number = roll_number
                        if dept_id:
                            profile.department = get_object_or_404(Department, id=dept_id)
                        if semester:
                            profile.semester = semester
                        profile.save()
                        messages.success(request, f"Student '{username}' added successfully.")
                    except Exception as e:
                        messages.error(request, f"Error adding student: {e}")
                
        elif action == 'edit':
            if student_id:
                if StudentProfile.objects.filter(roll_number=roll_number).exclude(user_id=student_id).exists():
                    messages.error(request, f"A student with roll number '{roll_number}' already exists.")
                elif CustomUser.objects.filter(username=username).exclude(id=student_id).exists() and username:
                    messages.error(request, f"A user with username '{username}' already exists.")
                elif CustomUser.objects.filter(email=email).exclude(id=student_id).exists() and email:
                    messages.error(request, f"A user with email '{email}' already exists.")
                else:
                    try:
                        user = get_object_or_404(CustomUser, id=student_id, role='Student')
                        if username: # sometimes username might not be editable, but just in case
                            user.username = username
                        user.full_name = full_name
                        user.email = email
                        user.save()
                        
                        profile = user.student_profile
                        profile.roll_number = roll_number
                        if dept_id:
                            profile.department = get_object_or_404(Department, id=dept_id)
                        if semester:
                            profile.semester = semester
                        profile.save()
                        messages.success(request, f"Student '{user.username}' updated successfully.")
                    except Exception as e:
                        messages.error(request, f"Error updating student: {e}")
                
        elif action == 'reset_password':
            if student_id and new_password:
                user = get_object_or_404(CustomUser, id=student_id, role='Student')
                user.set_password(new_password)
                user.save()
                
        elif action == 'delete':
            if student_id:
                CustomUser.objects.filter(id=student_id, role='Student').delete()
        
        return redirect('manage_students')

    search_query = request.GET.get('search', '')
    students = CustomUser.objects.filter(role='Student').select_related('student_profile', 'student_profile__department')
    
    if search_query:
        students = students.filter(
            Q(username__icontains=search_query) | 
            Q(full_name__icontains=search_query) |
            Q(student_profile__roll_number__icontains=search_query)
        )
    
    students = students.order_by('username')
    departments = Department.objects.all().order_by('name')
    
    context = {
        'students': students,
        'departments': departments,
        'search_query': search_query,
    }
    return render(request, 'organization/manage_students.html', context)

@login_required(login_url='role_selection')
def manage_faculty(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        faculty_uid = request.POST.get('faculty_uid')
        designation = request.POST.get('designation')
        dept_id = request.POST.get('dept_id')
        faculty_id = request.POST.get('faculty_id')
        subject_ids = request.POST.getlist('subject_ids')
        
        if action == 'add':
            if username and email and faculty_uid:
                if FacultyProfile.objects.filter(faculty_uid=faculty_uid).exists():
                    messages.error(request, f"A faculty with UID '{faculty_uid}' already exists.")
                elif CustomUser.objects.filter(username=username).exists():
                    messages.error(request, f"A user with username '{username}' already exists.")
                elif CustomUser.objects.filter(email=email).exists():
                    messages.error(request, f"A user with email '{email}' already exists.")
                else:
                    try:
                        # Create User
                        user = CustomUser.objects.create_user(
                            username=username,
                            email=email,
                            password='faculty123', # Default password
                            role='Faculty',
                            full_name=full_name
                        )
                        # Profile is created by signal, just update it
                        profile = user.faculty_profile
                        profile.faculty_uid = faculty_uid
                        profile.designation = designation
                        if dept_id:
                            profile.department = get_object_or_404(Department, id=dept_id)
                        profile.save()
                        
                        if subject_ids:
                            subjects = Subject.objects.filter(id__in=subject_ids)
                            profile.assigned_subjects.set(subjects)
                        messages.success(request, f"Faculty '{username}' added successfully.")
                    except Exception as e:
                        messages.error(request, f"Error adding faculty: {e}")
                
        elif action == 'edit':
            if faculty_id:
                if FacultyProfile.objects.filter(faculty_uid=faculty_uid).exclude(user_id=faculty_id).exists():
                    messages.error(request, f"A faculty with UID '{faculty_uid}' already exists.")
                elif CustomUser.objects.filter(username=username).exclude(id=faculty_id).exists() and username:
                    messages.error(request, f"A user with username '{username}' already exists.")
                elif CustomUser.objects.filter(email=email).exclude(id=faculty_id).exists() and email:
                    messages.error(request, f"A user with email '{email}' already exists.")
                else:
                    try:
                        user = get_object_or_404(CustomUser, id=faculty_id, role='Faculty')
                        if username: # username might not be editable, but just in case
                            user.username = username
                        user.full_name = full_name
                        user.email = email
                        user.save()
                        
                        profile = user.faculty_profile
                        profile.faculty_uid = faculty_uid
                        profile.designation = designation
                        if dept_id:
                            profile.department = get_object_or_404(Department, id=dept_id)
                        profile.save()
                        
                        if subject_ids:
                            subjects = Subject.objects.filter(id__in=subject_ids)
                            profile.assigned_subjects.set(subjects)
                        else:
                            profile.assigned_subjects.clear()
                        messages.success(request, f"Faculty '{user.username}' updated successfully.")
                    except Exception as e:
                        messages.error(request, f"Error updating faculty: {e}")
                
        elif action == 'delete':
            if faculty_id:
                CustomUser.objects.filter(id=faculty_id, role='Faculty').delete()
        
        return redirect('manage_faculty')

    search_query = request.GET.get('search', '')
    faculties = CustomUser.objects.filter(role='Faculty').select_related('faculty_profile', 'faculty_profile__department').prefetch_related('faculty_profile__assigned_subjects')
    
    if search_query:
        faculties = faculties.filter(
            Q(username__icontains=search_query) | 
            Q(full_name__icontains=search_query) |
            Q(faculty_profile__faculty_uid__icontains=search_query)
        )
    
    faculties = faculties.order_by('username')
    departments = Department.objects.all().order_by('name')
    subjects = Subject.objects.all().order_by('name')
    
    context = {
        'faculties': faculties,
        'departments': departments,
        'subjects': subjects,
        'search_query': search_query,
    }
    return render(request, 'organization/manage_faculty.html', context)

@login_required(login_url='role_selection')
def manage_complaints(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        complaint_id = request.POST.get('complaint_id')
        
        if action == 'delete':
            complaint = get_object_or_404(Complaint, id=complaint_id)
            complaint.delete()
            messages.success(request, "Complaint deleted successfully.")
        else:
            status = request.POST.get('status')
            admin_comments = request.POST.get('admin_comments')
            
            if complaint_id and status:
                complaint = get_object_or_404(Complaint, id=complaint_id)
                complaint.status = status
                if admin_comments is not None:
                    complaint.admin_comments = admin_comments
                complaint.save()
                messages.success(request, "Complaint status updated.")
            
        return redirect('manage_complaints')

    status_filter = request.GET.get('status', '')
    complaints = Complaint.objects.all().select_related('student').order_by('-created_at')
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
        
    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'status_choices': ['Pending', 'In Progress', 'Resolved', 'Rejected'],
    }
    return render(request, 'organization/manage_complaints.html', context)

@login_required(login_url='role_selection')
def manage_id_cards(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        user_role = request.POST.get('user_role')
        user_id = request.POST.get('user_id')
        
        # This POST will be used to update ID details like validity or address if needed
        if user_role == 'Student':
            profile = get_object_or_404(StudentProfile, user_id=user_id)
            profile.address = request.POST.get('address')
            profile.valid_from = request.POST.get('valid_from')
            profile.valid_till = request.POST.get('valid_till')
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
        elif user_role == 'Faculty':
            profile = get_object_or_404(FacultyProfile, user_id=user_id)
            profile.joining_date = request.POST.get('joining_date')
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            
        return redirect('manage_id_cards')

    search_query = request.GET.get('search', '')
    
    students = CustomUser.objects.filter(role='Student').select_related('student_profile', 'student_profile__department')
    faculties = CustomUser.objects.filter(role='Faculty').select_related('faculty_profile', 'faculty_profile__department')
    
    if search_query:
        students = students.filter(
            Q(username__icontains=search_query) | 
            Q(full_name__icontains=search_query) |
            Q(student_profile__roll_number__icontains=search_query)
        )
        faculties = faculties.filter(
            Q(username__icontains=search_query) | 
            Q(full_name__icontains=search_query) |
            Q(faculty_profile__faculty_uid__icontains=search_query)
        )
        
    context = {
        'students': students,
        'faculties': faculties,
        'search_query': search_query,
    }
    return render(request, 'organization/manage_id_cards.html', context)

@login_required(login_url='role_selection')
def generate_id_card(request, user_role, user_id):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if user_role == 'Student':
        user = get_object_or_404(CustomUser, id=user_id, role='Student')
        template = 'organization/id_card_student.html'
        context = {'student': user, 'profile': user.student_profile}
    elif user_role == 'Faculty':
        user = get_object_or_404(CustomUser, id=user_id, role='Faculty')
        template = 'organization/id_card_faculty.html'
        context = {'faculty': user, 'profile': user.faculty_profile}
    else:
        return redirect('manage_id_cards')
        
    return render(request, template, context)

@login_required(login_url='role_selection')
def manage_announcements(request):
    if request.user.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_role = request.POST.get('target_role', 'Both')
        dept_id = request.POST.get('department')
        semester = request.POST.get('semester')
        
        department = None
        if dept_id:
            department = get_object_or_404(Department, id=dept_id)
            
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
            target_role=target_role,
            department=department,
            semester=sem_val
        )
        messages.success(request, "Announcement published successfully!")
        return redirect('manage_announcements')

    announcements = Announcement.objects.all().order_by('-created_at')
    departments = Department.objects.all().order_by('name')
    
    context = {
        'announcements': announcements,
        'departments': departments,
        'semesters': range(1, 9),
    }
    return render(request, 'organization/manage_announcements.html', context)

@login_required(login_url='role_selection')
def delete_announcement(request, announcement_id):
    if request.user.role != 'Admin':
        return redirect('home')
        
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, "Announcement deleted successfully!")
    return redirect('manage_announcements')

@login_required(login_url='role_selection')
def manage_fees(request):
    if request.user.role != 'Admin':
        return redirect('home')

    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        action = request.POST.get('action')
        admin_comments = request.POST.get('admin_comments', '')
        payment = get_object_or_404(PaymentRecord, id=payment_id)

        if action == 'approve':
            payment.status = 'Approved'
            payment.admin_comments = admin_comments
            payment.save()
            try:
                profile = payment.student.student_profile
                from decimal import Decimal
                deduct = min(payment.amount, profile.fee_balance)
                profile.fee_balance = max(Decimal('0.00'), profile.fee_balance - deduct)
                profile.save()
            except Exception:
                pass
            messages.success(request, f'Payment #{payment.transaction_id} approved.')
        elif action == 'reject':
            payment.status = 'Rejected'
            payment.admin_comments = admin_comments
            payment.save()
            messages.warning(request, f'Payment #{payment.transaction_id} rejected.')
        return redirect('manage_fees')

    status_filter = request.GET.get('status', '')
    payments = PaymentRecord.objects.select_related('student', 'student__student_profile').order_by('-date')
    if status_filter:
        payments = payments.filter(status=status_filter)
    pending_count = PaymentRecord.objects.filter(status='Pending').count()
    approved_count = PaymentRecord.objects.filter(status='Approved').count()
    rejected_count = PaymentRecord.objects.filter(status='Rejected').count()
    context = {
        'payments': payments,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'organization/manage_fees.html', context)


@login_required(login_url='role_selection')
def manage_results(request):
    if request.user.role != 'Admin':
        return redirect('home')

    departments = Department.objects.all()
    subjects    = Subject.objects.all().select_related('department')
    students    = CustomUser.objects.filter(role='Student').select_related('student_profile')

    # Filters
    selected_dept = request.GET.get('dept', '')
    selected_sem  = request.GET.get('sem', '')

    if selected_dept:
        students = students.filter(student_profile__department_id=selected_dept)
        subjects = subjects.filter(department_id=selected_dept)
    if selected_sem:
        students = students.filter(student_profile__semester=selected_sem)

    # Handle POST — add / update a grade record
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_marks':
            student_id  = request.POST.get('student_id')
            subject_id  = request.POST.get('subject_id')
            semester    = request.POST.get('semester')
            marks       = request.POST.get('marks_obtained')
            max_marks   = request.POST.get('max_marks', 100)
            credits     = request.POST.get('credits', 3)
            exam_type   = request.POST.get('exam_type', 'Final')

            try:
                student = CustomUser.objects.get(id=student_id)
                subject = Subject.objects.get(id=subject_id)
                record, created = GradeRecord.objects.update_or_create(
                    student=student, subject=subject,
                    semester=semester, exam_type=exam_type,
                    defaults={
                        'marks_obtained': marks,
                        'max_marks': max_marks,
                        'credits': credits,
                    }
                )
                msg = 'Marks saved' if created else 'Marks updated'
                messages.success(request, f"{msg} for {student.username} — {subject.name}")
            except Exception as e:
                messages.error(request, f"Error saving marks: {e}")

        return redirect(f"{reverse('manage_results')}?dept={selected_dept}&sem={selected_sem}")

    # Build student result summary
    student_summaries = []
    for student in students:
        records = GradeRecord.objects.filter(
            student=student,
            **(({'semester': selected_sem}) if selected_sem else {})
        ).select_related('subject').order_by('semester', 'subject__name')

        total_pts = sum(float(r.grade_point) * int(r.credits) for r in records)
        total_crd = sum(int(r.credits) for r in records)
        cgpa = round(total_pts / total_crd, 2) if total_crd > 0 else 0.0

        profile = getattr(student, 'student_profile', None)
        student_summaries.append({
            'student':  student,
            'profile':  profile,
            'records':  records,
            'cgpa':     cgpa,
            'total_subjects': records.count(),
        })

    context = {
        'departments':        departments,
        'subjects':           subjects,
        'student_summaries':  student_summaries,
        'selected_dept':      selected_dept,
        'selected_sem':       selected_sem,
        'exam_type_choices':  GradeRecord.EXAM_TYPE_CHOICES,
        'semesters':          range(1, 9),
    }
    return render(request, 'organization/manage_results.html', context)


@login_required(login_url='role_selection')
def delete_grade_record(request, record_id):
    if request.user.role != 'Admin':
        return redirect('home')
    record = get_object_or_404(GradeRecord, id=record_id)
    student_name = record.student.username
    subject_name = record.subject.name if record.subject else 'N/A'
    record.delete()
    messages.success(request, f"Deleted marks for {student_name} — {subject_name}")
    return redirect('manage_results')


@login_required(login_url='role_selection')
def manage_requests(request):
    if request.user.role != 'Admin':
        return redirect('home')

    # --- POST: Approve / Reject ---
    if request.method == 'POST':
        action     = request.POST.get('action')
        request_id = request.POST.get('request_id')
        req_obj    = get_object_or_404(StudentRequest, id=request_id)
        if action == 'approve':
            req_obj.status = 'Approved'
            req_obj.save()
            messages.success(request, f"Request by {req_obj.student.username} has been Approved.")
        elif action == 'reject':
            req_obj.status = 'Rejected'
            req_obj.save()
            messages.warning(request, f"Request by {req_obj.student.username} has been Rejected.")
        return redirect(request.get_full_path())

    # --- GET: Filter ---
    type_filter   = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    search_q      = request.GET.get('q', '')

    requests_qs = StudentRequest.objects.select_related(
        'student', 'student__student_profile', 'student__student_profile__department'
    ).order_by('-created_at')

    if type_filter:
        requests_qs = requests_qs.filter(request_type=type_filter)
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    if search_q:
        requests_qs = requests_qs.filter(
            Q(student__username__icontains=search_q) |
            Q(student__full_name__icontains=search_q)
        )

    all_qs = StudentRequest.objects.all()
    context = {
        'requests':       requests_qs,
        'total_count':    all_qs.count(),
        'pending_count':  all_qs.filter(status='Pending').count(),
        'approved_count': all_qs.filter(status='Approved').count(),
        'rejected_count': all_qs.filter(status='Rejected').count(),
        'type_filter':    type_filter,
        'status_filter':  status_filter,
        'search_q':       search_q,
    }
    return render(request, 'organization/manage_requests.html', context)
