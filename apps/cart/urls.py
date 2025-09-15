from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_cart, name='get_cart'),
    path('items/add', views.add_to_cart, name='add_to_cart'),
    path('items/delete', views.delete_from_cart, name='delete_from_cart'),
    path('items/update', views.update_cart_item, name='update_cart_item'),
    path('clear/', views.clear_cart, name='clear_cart'),
]
