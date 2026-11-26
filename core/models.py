from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='📌')
    color = models.CharField(max_length=20, default='#FF6B35')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Department(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Challenge(models.Model):
    STATUS_OPEN = 'open'
    STATUS_VERIFIED = 'verified'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='challenges')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='challenges')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    location_name = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def vote_count(self):
        return self.votes.count()

    def comment_count(self):
        return self.comments.count()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class ChallengeImage(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='challenges/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Image for {self.challenge.title}'


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'challenge')

    def __str__(self):
        return f'{self.user.username} voted on {self.challenge.title}'


class Comment(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username}: {self.text[:40]}'


class StatusHistory(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']

    def __str__(self):
        return f'{self.challenge.title}: {self.old_status} -> {self.new_status}'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Notification for {self.user.username}'
