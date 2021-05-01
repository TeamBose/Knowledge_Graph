from django.shortcuts import render
from .forms import InputForm
from .pipeline import execute
from json import dumps
from django.contrib import messages
# Create your views here.

def fire(request):
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

    return render(request, 'hello_world.html', {"query": query, "data":data})