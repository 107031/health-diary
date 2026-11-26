from .observations import observations
from .summary import summary
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
]

urlpatterns += [
    path('habits/', views.habits, name='habits'),
    path('entries/save/', views.save_day, name='save_day'),
]

urlpatterns.append(path('stats/summary/', summary, name='stats_summary'))

urlpatterns.append(path('observations/', observations, name='observations'))
