from django.shortcuts import render , redirect
from django.urls import reverse
from .models import User

from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreateForm

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.

def create(request):
    if request.method == 'GET':
        return render(
            request,
            "login/create.html",
            {"form":CustomUserCreateForm()}
        )
    elif request.method == "POST":
        form = CustomUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect(reverse('home'))
        else:
            return render(request, "login/create.html",{"form":form})

def user_login(request):
    if request.method == "GET":
        return render(request,
                      'login/login.html',
                      {'form':AuthenticationForm()})
    elif request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username , password=password)
        if user is not None :
            login(request, user)
            return redirect(reverse("home"))
        else :
            return render(
                request,
                'login/login.html',
                {'form': AuthenticationForm(),
                "errorMessage":"ID나 Password를 다시 확인하세요."}
            )