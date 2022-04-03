import os

from django.shortcuts import render, redirect

from content.models import Content

# Create your views here.

def home(request):
    content = Content.objects.filter(name='Home').first()
    return render(request, 'client/Home.html', {
        'content': content
    })
    return render(request, 'v2/base.html', {})

def redirect_home(request):
    return redirect('client:home')


""" Authentication/Login """
def login(request):
    return render (request, 'client/Login/index.html')


""" User Dashboard """
def user_dashboard_profile(request, pk):
    return render(request, 'client/User/profile.html', {})
    return render(request, 'v2/UserDashboard/profile.html', {})

def user_dashboard_family(request):
    return render(request, 'v2/UserDashboard/family.html', {})


""" Shop """
""" See acm.views """

""" Mngt """

def mngt_products (request):
    return render (request, 'client/Mngt/Products.html', {}) 