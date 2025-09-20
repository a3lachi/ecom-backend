from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review-list'),
    path('create/', views.CreateReviewView.as_view(), name='review-create'),
]
