from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

app_name="login"

urlpatterns = [
    path("create/", views.create, name="create"),
    path("login",
         LoginView.as_view(
             template_name = "login/login.html",
             form_class = AuthenticationForm
         ),
         name="login")
]