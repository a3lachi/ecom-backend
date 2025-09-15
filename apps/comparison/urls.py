from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_comparison, name='get_comparison'),
    path('add/', views.add_to_comparison, name='add_to_comparison'),
    path('remove/', views.remove_from_comparison, name='remove_from_comparison'),
    path('clear/', views.clear_comparison, name='clear_comparison'),
]