from django.shortcuts import render
#from .forms import InputForm
#from .pipeline import execute
from json import dumps
from django.contrib import messages
# Create your views here.

def fire(request):


    return render(request, 'layouts/base.html', {"query": "query", "data":"data"})