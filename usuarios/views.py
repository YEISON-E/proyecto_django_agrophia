# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from django.contrib.auth.views import LoginView

class Logueo(LoginView):
    template_name = "components/forloggin.html"
    redirect_authenticated_user = True

