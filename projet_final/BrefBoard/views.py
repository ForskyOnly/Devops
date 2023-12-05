from django.shortcuts import render, redirect

# Create your views here.

def home(request) : 
    render(request,'home.html')