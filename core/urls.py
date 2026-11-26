from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Public
    path('', views.home, name='home'),
    path('explore/', views.explore, name='explore'),
    path('challenge/<int:pk>/', views.challenge_detail, name='challenge_detail'),
    path('challenge/<int:pk>/vote/', views.vote, name='vote'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('map/', views.map_view, name='map'),

    # Citizen
    path('dashboard/', views.dashboard, name='dashboard'),
    path('submit/', views.submit_challenge, name='submit_challenge'),
    path('my-challenges/', views.my_challenges, name='my_challenges'),
    path('notifications/', views.notifications_view, name='notifications'),

    # Admin panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/challenges/', views.admin_challenges, name='admin_challenges'),
    path('admin-panel/challenges/<int:pk>/update/', views.admin_update_challenge, name='admin_update_challenge'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/analytics/', views.admin_analytics, name='admin_analytics'),
]
