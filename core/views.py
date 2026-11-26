import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from .complaint_log import append_complaint_record
from .models import Category, Department, Challenge, ChallengeImage, Vote, Comment, StatusHistory, Notification


logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def notify(user, message, challenge=None):
    Notification.objects.create(user=user, message=message, challenge=challenge)


# ── Auth ─────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST.get('email', '')
        password = request.POST['password']
        full_name = request.POST.get('full_name', '')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            if full_name:
                parts = full_name.split(' ', 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
                user.save()
            login(request, user)
            messages.success(request, f'Welcome to CivicConnect, {user.username}!')
            return redirect('dashboard')
    return render(request, 'auth/register.html')


def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# ── Public pages ──────────────────────────────────────────────────────────────

def home(request):
    recent = Challenge.objects.select_related('category', 'author').filter(status__in=['open', 'verified', 'in_progress'])[:6]
    resolved = Challenge.objects.filter(status='resolved').count()
    total = Challenge.objects.count()
    categories = Category.objects.annotate(count=Count('challenges')).order_by('-count')
    stats = {
        'total': total,
        'resolved': resolved,
        'open': Challenge.objects.filter(status='open').count(),
        'in_progress': Challenge.objects.filter(status='in_progress').count(),
    }
    return render(request, 'public/home.html', {'recent': recent, 'stats': stats, 'categories': categories})


def explore(request):
    qs = Challenge.objects.select_related('category', 'author').annotate(vote_c=Count('votes'))
    q = request.GET.get('q', '')
    cat = request.GET.get('category', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'newest')

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(location_name__icontains=q))
    if cat:
        qs = qs.filter(category_id=cat)
    if status:
        qs = qs.filter(status=status)

    if sort == 'votes':
        qs = qs.order_by('-vote_c')
    elif sort == 'oldest':
        qs = qs.order_by('created_at')
    else:
        qs = qs.order_by('-created_at')

    categories = Category.objects.all()
    return render(request, 'public/explore.html', {
        'challenges': qs,
        'categories': categories,
        'q': q, 'selected_cat': cat, 'selected_status': status, 'sort': sort,
        'status_choices': Challenge.STATUS_CHOICES,
    })


def challenge_detail(request, pk):
    challenge = get_object_or_404(Challenge.objects.select_related('category', 'author', 'department'), pk=pk)
    comments = challenge.comments.select_related('author').all()
    history = challenge.history.select_related('changed_by').all()
    images = challenge.images.all()
    user_voted = request.user.is_authenticated and challenge.votes.filter(user=request.user).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('comment', '').strip()
        if text:
            Comment.objects.create(challenge=challenge, author=request.user, text=text)
            if challenge.author != request.user:
                notify(challenge.author, f'{request.user.username} commented on your challenge "{challenge.title}"', challenge)
            return redirect('challenge_detail', pk=pk)

    return render(request, 'public/challenge_detail.html', {
        'challenge': challenge,
        'comments': comments,
        'history': history,
        'images': images,
        'user_voted': user_voted,
    })


def leaderboard(request):
    top_users = (
        User.objects.annotate(
            challenge_count=Count('challenges', distinct=True),
            vote_count=Count('challenges__votes', distinct=True),
        )
        .filter(challenge_count__gt=0)
        .order_by('-vote_count')[:20]
    )
    return render(request, 'public/leaderboard.html', {'top_users': top_users})


def map_view(request):
    import json
    challenges = Challenge.objects.filter(latitude__isnull=False).select_related('category')
    data = [{
        'id': c.pk,
        'title': c.title,
        'lat': c.latitude,
        'lng': c.longitude,
        'status': c.status,
        'category': c.category.name if c.category else '',
        'icon': c.category.icon if c.category else '📌',
    } for c in challenges]
    return render(request, 'public/map.html', {'challenges_json': json.dumps(data)})


# ── Voting ────────────────────────────────────────────────────────────────────

@login_required
def vote(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    vote_obj, created = Vote.objects.get_or_create(user=request.user, challenge=challenge)
    if not created:
        vote_obj.delete()
        voted = False
    else:
        voted = True
        if challenge.author != request.user:
            notify(challenge.author, f'{request.user.username} upvoted your challenge "{challenge.title}"', challenge)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'voted': voted, 'count': challenge.vote_count()})
    return redirect('challenge_detail', pk=pk)


# ── Citizen dashboard ─────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    my_challenges = Challenge.objects.filter(author=request.user).annotate(vote_c=Count('votes')).order_by('-created_at')
    my_votes = Vote.objects.filter(user=request.user).select_related('challenge').order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    stats = {
        'total': my_challenges.count(),
        'resolved': my_challenges.filter(status='resolved').count(),
        'open': my_challenges.filter(status='open').count(),
        'votes_received': Vote.objects.filter(challenge__author=request.user).count(),
    }
    return render(request, 'citizen/dashboard.html', {
        'my_challenges': my_challenges[:8],
        'my_votes': my_votes,
        'stats': stats,
        'unread_count': unread_count,
    })


@login_required
def submit_challenge(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        category_id = request.POST.get('category')
        location_name = request.POST.get('location_name', '')
        state = request.POST.get('state', '')
        if state and location_name:
            location_name = f"{location_name}, {state}"
        elif state:
            location_name = state
        latitude = request.POST.get('latitude') or None
        longitude = request.POST.get('longitude') or None

        challenge = Challenge.objects.create(
            title=title,
            description=description,
            category_id=category_id if category_id else None,
            author=request.user,
            location_name=location_name,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
        )
        StatusHistory.objects.create(
            challenge=challenge, changed_by=request.user,
            old_status='', new_status='open', note='Challenge submitted.'
        )
        for img in request.FILES.getlist('images'):
            ChallengeImage.objects.create(challenge=challenge, image=img)

        try:
            append_complaint_record(challenge)
        except OSError:
            logger.exception('Could not append complaint %s to the JSON log.', challenge.pk)
            messages.error(
                request,
                'Your report was saved, but the complaint log file could not be updated.',
            )
        else:
            messages.success(request, 'Challenge submitted successfully!')

        return redirect('challenge_detail', pk=challenge.pk)

    return render(request, 'citizen/submit_challenge.html', {'categories': categories})


@login_required
def my_challenges(request):
    challenges = Challenge.objects.filter(author=request.user).annotate(vote_c=Count('votes')).order_by('-created_at')
    return render(request, 'citizen/my_challenges.html', {'challenges': challenges})


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'citizen/notifications.html', {'notifications': notifs})


# ── Admin dashboard ───────────────────────────────────────────────────────────

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    stats = {
        'total': Challenge.objects.count(),
        'open': Challenge.objects.filter(status='open').count(),
        'verified': Challenge.objects.filter(status='verified').count(),
        'in_progress': Challenge.objects.filter(status='in_progress').count(),
        'resolved': Challenge.objects.filter(status='resolved').count(),
        'rejected': Challenge.objects.filter(status='rejected').count(),
        'users': User.objects.filter(is_staff=False).count(),
    }
    recent = Challenge.objects.select_related('category', 'author').order_by('-created_at')[:10]
    cat_data = Category.objects.annotate(count=Count('challenges')).order_by('-count')
    return render(request, 'admin_panel/dashboard.html', {'stats': stats, 'recent': recent, 'cat_data': cat_data})


@admin_required
def admin_challenges(request):
    qs = Challenge.objects.select_related('category', 'author', 'department').annotate(vote_c=Count('votes'))
    status_filter = request.GET.get('status', '')
    cat_filter = request.GET.get('category', '')
    q = request.GET.get('q', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if cat_filter:
        qs = qs.filter(category_id=cat_filter)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(author__username__icontains=q))
    categories = Category.objects.all()
    departments = Department.objects.all()
    return render(request, 'admin_panel/challenges.html', {
        'challenges': qs.order_by('-created_at'),
        'categories': categories,
        'departments': departments,
        'status_choices': Challenge.STATUS_CHOICES,
        'status_filter': status_filter,
        'cat_filter': cat_filter,
        'q': q,
    })


@admin_required
def admin_update_challenge(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        old_status = challenge.status
        new_status = request.POST.get('status', challenge.status)
        note = request.POST.get('note', '')
        dept_id = request.POST.get('department')
        is_verified = request.POST.get('is_verified') == 'on'

        challenge.status = new_status
        challenge.is_verified = is_verified
        challenge.department_id = dept_id if dept_id else None
        challenge.save()

        if old_status != new_status:
            StatusHistory.objects.create(
                challenge=challenge, changed_by=request.user,
                old_status=old_status, new_status=new_status, note=note
            )
            notify(challenge.author,
                   f'Your challenge "{challenge.title}" status changed to {new_status.replace("_", " ").title()}.',
                   challenge)

        messages.success(request, 'Challenge updated.')
        return redirect('admin_challenges')

    departments = Department.objects.all()
    return render(request, 'admin_panel/update_challenge.html', {
        'challenge': challenge,
        'departments': departments,
        'status_choices': Challenge.STATUS_CHOICES,
    })


@admin_required
def admin_users(request):
    users = User.objects.filter(is_staff=False).annotate(
        challenge_count=Count('challenges', distinct=True),
        vote_count=Count('votes', distinct=True),
    ).order_by('-challenge_count')
    return render(request, 'admin_panel/users.html', {'users': users})


@admin_required
def admin_analytics(request):
    from django.db.models.functions import TruncMonth
    from django.db.models import Count
    monthly = (
        Challenge.objects.annotate(month=TruncMonth('created_at'))
        .values('month').annotate(count=Count('id')).order_by('month')
    )
    cat_data = Category.objects.annotate(count=Count('challenges')).order_by('-count')
    status_data = {s[0]: Challenge.objects.filter(status=s[0]).count() for s in Challenge.STATUS_CHOICES}
    return render(request, 'admin_panel/analytics.html', {
        'monthly': list(monthly),
        'cat_data': cat_data,
        'status_data': status_data,
    })
