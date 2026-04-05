from datetime import date, timedelta

from django.core.management.base import BaseCommand

from attendance.models import (
    Attendance,
    AttendanceRecord,
    Faculty,
    Student,
    Subject,
    User,
)


class Command(BaseCommand):
    help = 'Seed sample data for the attendance monitoring system.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...')

        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if not admin_user.has_usable_password():
            admin_user.set_password('adminpass')
            admin_user.save()

        faculty_user, _ = User.objects.get_or_create(
            username='faculty1',
            defaults={
                'email': 'faculty1@example.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'role': User.ROLE_FACULTY,
            },
        )
        if not faculty_user.has_usable_password():
            faculty_user.set_password('faculty123')
            faculty_user.save()

        faculty, _ = Faculty.objects.get_or_create(user=faculty_user, defaults={'department': 'Computer Science'})

        student_users = []
        students = []
        for roll, username, first_name, last_name, class_name in [
            ('CS001', 'student1', 'Anita', 'Kumar', 'CS-A'),
            ('CS002', 'student2', 'Rohit', 'Verma', 'CS-A'),
            ('CS003', 'student3', 'Neha', 'Patel', 'CS-B'),
        ]:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': User.ROLE_STUDENT,
                },
            )
            if not user.has_usable_password():
                user.set_password('student123')
                user.save()
            student_users.append(user)
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={'roll_number': roll, 'class_name': class_name, 'enrollment_year': '2024'},
            )
            students.append(student)

        subjects = []
        for code, name, class_name in [
            ('CS101', 'Programming Fundamentals', 'CS-A'),
            ('CS102', 'Database Systems', 'CS-B'),
        ]:
            subject, _ = Subject.objects.get_or_create(
                code=code,
                defaults={'name': name, 'faculty': faculty, 'class_name': class_name, 'credits': 3},
            )
            subjects.append(subject)

        start_date = date.today() - timedelta(days=7)
        for offset in range(5):
            current_date = start_date + timedelta(days=offset)
            for subject in subjects:
                attendance, _ = Attendance.objects.get_or_create(
                    subject=subject,
                    date=current_date,
                    defaults={'created_by': faculty},
                )
                for student in students:
                    status = AttendanceRecord.STATUS_PRESENT if student.class_name == subject.class_name else AttendanceRecord.STATUS_ABSENT
                    AttendanceRecord.objects.update_or_create(
                        attendance=attendance,
                        student=student,
                        defaults={'status': status},
                    )

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully.'))
