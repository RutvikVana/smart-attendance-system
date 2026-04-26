from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_FACULTY = 'faculty'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_FACULTY, 'Faculty'),
        (ROLE_STUDENT, 'Student'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def is_faculty(self):
        return self.role == self.ROLE_FACULTY

    def is_student(self):
        return self.role == self.ROLE_STUDENT


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    class_name = models.CharField(max_length=100, blank=True)
    enrollment_year = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class Subject(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='subjects')
    class_name = models.CharField(max_length=100, blank=True)
    credits = models.PositiveSmallIntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Attendance(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    created_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='created_attendances')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subject', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.subject.code} - {self.date}"

    def present_count(self):
        return self.records.filter(status=AttendanceRecord.STATUS_PRESENT).count()

    def absent_count(self):
        return self.records.filter(status=AttendanceRecord.STATUS_ABSENT).count()


class AttendanceRecord(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
    ]

    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ABSENT)

    class Meta:
        unique_together = ('attendance', 'student')

    def __str__(self):
        return f"{self.student} - {self.get_status_display()}"


def compute_attendance_percentage(student, subject=None):
    records = student.attendance_records.select_related('attendance__subject')
    if subject:
        records = records.filter(attendance__subject=subject)
    total = records.count()
    if total == 0:
        return 0
    present = records.filter(status=AttendanceRecord.STATUS_PRESENT).count()
    return round((present / total) * 100, 2)


def compute_risk(attendance_percent):
    if attendance_percent < 50:
        return 'High Risk'
    if attendance_percent < 75:
        return 'Medium Risk'
    return 'Low Risk'
