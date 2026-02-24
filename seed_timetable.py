import os
import django
import random
from datetime import timedelta, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ums_project.settings')
django.setup()

from core.models import Subject, Department, CustomUser, TimeTableRecord, AttendanceRecord, LearningMaterial

def seed_data():
    print("Clearing old subjects, timetable, and attendance records...")
    Subject.objects.all().delete()
    TimeTableRecord.objects.all().delete()
    AttendanceRecord.objects.all().delete()
    LearningMaterial.objects.all().delete()

    cs_dept, _ = Department.objects.get_or_create(name='Computer Science')

    faculty_member = CustomUser.objects.filter(role='Faculty').first()
    students = CustomUser.objects.filter(role='Student')

    if not faculty_member:
        print("No faculty found in the database. Please create one.")
        return
    if not students.exists():
        print("No students found in the database. Please create some.")
        return

    print("Creating realistic subjects...")
    subjects_data = [
        ("Database Management Systems", "DBMS"),
        ("Operating Systems", "OS"),
        ("Data Structures and Algorithms", "DSA"),
        ("Computer Networks", "CN"),
        ("Software Engineering", "SE"),
    ]

    subjects = []
    for name, code in subjects_data:
        sub = Subject.objects.create(name=name, code=code, department=cs_dept)
        subjects.append(sub)

    # Assign subjects to faculty
    if hasattr(faculty_member, 'faculty_profile'):
        faculty_member.faculty_profile.department = cs_dept
        faculty_member.faculty_profile.save()
        faculty_member.faculty_profile.assigned_subjects.set(subjects)

    # Assign students to CS dept
    for student in students:
        if hasattr(student, 'student_profile'):
            student.student_profile.department = cs_dept
            student.student_profile.save()

    print("Creating Monday-Friday Timetable...")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = [
        ("09:00:00", "10:00:00"),
        ("10:00:00", "11:00:00"),
        ("11:30:00", "12:30:00"),
        ("13:30:00", "14:30:00"),
    ]
    rooms = ["Room 101", "Room 102", "Lab A", "Lab B"]

    # Specifically ensure DBMS, OS, DSA are on Monday
    monday_subs = [
        next(s for s in subjects if s.code == "DBMS"),
        next(s for s in subjects if s.code == "OS"),
        next(s for s in subjects if s.code == "DSA"),
        next(s for s in subjects if s.code == "CN")
    ]

    for day in days:
        if day == 'Monday':
            daily_subs = monday_subs
        else:
            daily_subs = random.sample(subjects, 4)
            
        for i in range(len(daily_subs)):
            TimeTableRecord.objects.create(
                department=cs_dept,
                semester=1,
                day=day,
                subject=daily_subs[i],
                faculty=faculty_member,
                start_time=times[i][0],
                end_time=times[i][1],
                room=rooms[i]
            )

    print("Seeding past 30 days of attendance...")
    today = date.today()
    for i in range(30):
        past_date = today - timedelta(days=i)
        day_name = past_date.strftime("%A")
        
        if day_name in days:
            classes_that_day = TimeTableRecord.objects.filter(day=day_name)
            for cls in classes_that_day:
                for student in students:
                    is_present = random.random() < 0.85 # 85% attendance rate
                    AttendanceRecord.objects.create(
                        student=student,
                        subject=cls.subject,
                        date=past_date,
                        status=is_present
                    )

    print("Database successfully seeded with new realistic subjects, timetable, and attendance records!")

if __name__ == "__main__":
    seed_data()
