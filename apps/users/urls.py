from django.urls import path
from .views import UserMeView, UserAddressListView

urlpatterns = [
    # User profile endpoints
    path('me/', UserMeView.as_view(), name='user-me'),
    
    # User address endpoints
    path('me/addresses/', UserAddressListView.as_view(), name='user-addresses'),
]
