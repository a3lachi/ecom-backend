from django.urls import path
from . import views

urlpatterns = [
    # Public endpoint for submitting contact form
    path('submit/', views.CreateContactView.as_view(), name='contact-submit'),
    
    # Admin endpoints for managing contact inquiries
    path('', views.ContactListView.as_view(), name='contact-list'),
    path('<int:pk>/', views.ContactDetailView.as_view(), name='contact-detail'),
]