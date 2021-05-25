# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from django import template
from .forms import InputForm
from .pipeline import execute

from json import dumps
def index(request):

    query = "no query"
    data= {
        "nodes": None,
        "links": None,
    }
    data = dumps(data)
    if request.method == "POST":
        # Get the posted form
        MyForm = InputForm(request.POST)

        if MyForm.is_valid():
            query = MyForm.cleaned_data['query']
            #messages.info(request, 'query entered!')
            data=execute(request=request,nl_query=query)
            data = dumps(data)
    else:
        MyForm = InputForm()

    context = {}
    context['segment'] = 'index'

    html_template = loader.get_template( 'index.html' )
    #return HttpResponse(html_template.render(context, request))

    return render(request, 'index.html', {"query": query, "data":data})


def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template
        
        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:
    
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))
