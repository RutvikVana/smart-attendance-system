from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Attendance, AttendanceRecord, Faculty, Subject, Student, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Role Details', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'class_name', 'enrollment_year')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'roll_number')
    list_filter = ('class_name',)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty', 'class_name', 'credits')
    list_filter = ('class_name', 'faculty')
    search_fields = ('name', 'code')


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('subject', 'date', 'created_by', 'present_count', 'absent_count')
    list_filter = ('subject', 'date')
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'student', 'status')
    list_filter = ('status', 'attendance__subject')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name')
