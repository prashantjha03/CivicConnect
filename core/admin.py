from django.contrib import admin
from .models import Category, Department, Challenge, ChallengeImage, Vote, Comment, StatusHistory, Notification


class ChallengeImageInline(admin.TabularInline):
    model = ChallengeImage
    extra = 1


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ['changed_by', 'old_status', 'new_status', 'changed_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_verified', 'vote_count', 'created_at']
    list_filter = ['status', 'is_verified', 'category']
    search_fields = ['title', 'description', 'author__username']
    inlines = [ChallengeImageInline, StatusHistoryInline]
    list_editable = ['status', 'is_verified']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'challenge', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
