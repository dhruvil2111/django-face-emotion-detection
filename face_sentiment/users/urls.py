from django.urls import path
from .views import register, login_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("register/", register, name="register"),
    path("", login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
