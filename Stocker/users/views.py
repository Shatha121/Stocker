from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


# Create your views here.

def login(request:HttpResponse):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")
        user = authenticate(request, username=identifier, password=password)

        if user == None:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            login(request,user)
            if user.is_superuser:
                return redirect("users:admin_dashboard")
            else:
                return redirect(request.GET.get("next","/"))
        else:
            messages.error(request,"There is no user with these information", "alert-danger")

    return render(request, "users/login.html", {})

def log_out(request:HttpRequest):
    logout(request)
    return redirect("users:login")