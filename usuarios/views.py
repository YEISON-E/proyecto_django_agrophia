from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def inicio(request):
    return HttpResponse("La app CORE está funcionando correctamente 😄")
