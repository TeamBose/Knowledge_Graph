from django import forms
from django.contrib import messages

class InputForm(forms.Form):
    query = forms.CharField(max_length=200)