from django.urls import path
from visualizer import views

urlpatterns = [
    path('', views.fire, name='fire'),
]