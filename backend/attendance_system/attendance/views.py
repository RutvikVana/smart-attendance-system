from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AttendanceMarkForm, LoginForm
from .models import (
    Attendance,
    AttendanceRecord,
    Faculty,
    Subject,
    Student,
    User,
    compute_attendance_percentage,
    compute_risk,
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password')
    return render(request, 'attendance/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.warning(request, 'You do not have permission to access that page.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


@login_required
def dashboard(request):
    user = request.user
    if user.is_admin():
        students = Student.objects.all()
        subjects = Subject.objects.all()
        total_attendance = AttendanceRecord.objects.count()
        at_risk = []
        for student in students:
            percent = compute_attendance_percentage(student)
            if percent < 75:
                at_risk.append({'student': student, 'percent': percent, 'risk': compute_risk(percent)})
        class_counts = {
            group: students.filter(class_name=group).count()
            for group in students.values_list('class_name', flat=True).distinct()
            if group
        }
        return render(
            request,
            'attendance/dashboard_admin.html',
            {
                'students': students,
                'subjects': subjects,
                'total_attendance': total_attendance,
                'at_risk': at_risk,
                'class_counts': class_counts,
            },
        )
    if user.is_faculty():
        faculty = get_object_or_404(Faculty, user=user)
        subjects = Subject.objects.filter(faculty=faculty)
        attendance_sessions = Attendance.objects.filter(created_by=faculty)[:10]
        return render(
            request,
            'attendance/dashboard_faculty.html',
            {'subjects': subjects, 'attendance_sessions': attendance_sessions},
        )
    if user.is_student():
        student = get_object_or_404(Student, user=user)
        percent = compute_attendance_percentage(student)
        risk = compute_risk(percent)
        subject_list = Subject.objects.filter(class_name=student.class_name)
        subject_breakdown = []
        for subject in subject_list:
            percent_subject = compute_attendance_percentage(student, subject=subject)
            subject_breakdown.append({'subject': subject, 'percent': percent_subject})
        return render(
            request,
            'attendance/dashboard_student.html',
            {'student': student, 'percent': percent, 'risk': risk, 'subject_breakdown': subject_breakdown},
        )
    return redirect('login')


@login_required
@role_required(['faculty'])
def mark_attendance(request):
    faculty = get_object_or_404(Faculty, user=request.user)
    form = AttendanceMarkForm(request.POST or None, faculty=faculty)
    subject = None
    students = []
    selected_subject_id = request.GET.get('subject') or request.POST.get('subject')

    if request.method == 'POST' and form.is_valid():
        subject = form.cleaned_data['subject']
        attendance_date = form.cleaned_data['attendance_date']
        attendance, created = Attendance.objects.get_or_create(
            subject=subject,
            date=attendance_date,
            defaults={'created_by': faculty},
        )
        students = Student.objects.filter(class_name=subject.class_name)
        for student in students:
            status_key = f'status_{student.id}'
            status = request.POST.get(status_key, AttendanceRecord.STATUS_ABSENT)
            AttendanceRecord.objects.update_or_create(
                attendance=attendance,
                student=student,
                defaults={'status': status},
            )
        messages.success(request, 'Attendance has been saved successfully.')
        return redirect('mark_attendance')

    if selected_subject_id:
        subject = get_object_or_404(Subject, id=selected_subject_id)
        students = Student.objects.filter(class_name=subject.class_name)

    return render(
        request,
        'attendance/mark_attendance.html',
        {'form': form, 'subject': subject, 'students': students},
    )


@login_required
def analytics(request):
    students = Student.objects.all()
    subjects = Subject.objects.all()
    subject_id = request.GET.get('subject')
    selected_subject = None
    if subject_id:
        selected_subject = get_object_or_404(Subject, id=subject_id)
    student_stats = []
    for student in students:
        percent = compute_attendance_percentage(student, subject=selected_subject)
        student_stats.append(
            {
                'student': student,
                'percent': percent,
                'risk': compute_risk(percent),
            }
        )
    subject_analysis = []
    for subject in subjects:
        total_records = AttendanceRecord.objects.filter(attendance__subject=subject).count()
        present_records = AttendanceRecord.objects.filter(attendance__subject=subject, status=AttendanceRecord.STATUS_PRESENT).count()
        average_percent = round((present_records / total_records) * 100, 2) if total_records else 0
        subject_analysis.append({'subject': subject, 'average_percent': average_percent})

    continuous_absent = []
    risk_counts = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
    for student in students:
        records = AttendanceRecord.objects.filter(student=student).order_by('attendance__date')
        streak = 0
        max_streak = 0
        for record in records:
            if record.status == AttendanceRecord.STATUS_ABSENT:
                streak += 1
            else:
                max_streak = max(max_streak, streak)
                streak = 0
        max_streak = max(max_streak, streak)
        if max_streak >= 3:
            continuous_absent.append({'student': student, 'streak': max_streak})

    for item in student_stats:
        risk_counts[item['risk']] += 1
    at_risk_count = risk_counts['Medium Risk'] + risk_counts['High Risk']

    return render(
        request,
        'attendance/analytics.html',
        {
            'student_stats': student_stats,
            'subject_analysis': subject_analysis,
            'continuous_absent': continuous_absent,
            'selected_subject': selected_subject,
            'subjects': subjects,
            'risk_counts': risk_counts,
            'at_risk_count': at_risk_count,
        },
    )


@login_required
def student_report(request, student_id=None):
    if request.user.role == User.ROLE_STUDENT:
        student = get_object_or_404(Student, user=request.user)
    else:
        student = get_object_or_404(Student, id=student_id) if student_id else None
    if student is None:
        messages.error(request, 'Student record not found.')
        return redirect('dashboard')

    records = AttendanceRecord.objects.filter(student=student).select_related('attendance__subject')
    subject_summary = {}
    for record in records:
        subject = record.attendance.subject
        if subject not in subject_summary:
            subject_summary[subject] = {'present': 0, 'total': 0}
        if record.status == AttendanceRecord.STATUS_PRESENT:
            subject_summary[subject]['present'] += 1
        subject_summary[subject]['total'] += 1

    summary = []
    for subject, stats in subject_summary.items():
        percent = round((stats['present'] / stats['total']) * 100, 2) if stats['total'] else 0
        summary.append({'subject': subject, 'present': stats['present'], 'total': stats['total'], 'percent': percent})

    overall_percent = compute_attendance_percentage(student)
    risk = compute_risk(overall_percent)
    return render(
        request,
        'attendance/student_report.html',
        {
            'student': student,
            'overall_percent': overall_percent,
            'risk': risk,
            'summary': summary,
            'records': records,
        },
    )
