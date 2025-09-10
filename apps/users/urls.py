from django.urls import path
from .views import UserMeView

urlpatterns = [
    # User profile endpoints
    path('me/', UserMeView.as_view(), name='user-me'),
]
