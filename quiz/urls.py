from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('toggle-ai/', views.toggle_ai_view, name='toggle_ai'),
    path('start/', views.start_view, name='start'),
    path('question/', views.question_view, name='question'),
    path('submit/', views.submit_view, name='submit'),
    path('result/', views.result_view, name='result'),
    path('profile/', views.profile_view, name='profile'), 
]