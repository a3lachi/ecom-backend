from django.urls import path
from . import views

urlpatterns = [
    # Payment management
    path('methods/', views.list_payment_methods, name='list_payment_methods'),
    path('create/', views.create_payment, name='create_payment'),
    path('status/<str:payment_id>/', views.get_payment_status, name='get_payment_status'),
    
    # PayPal callback URLs
    path('paypal/success/', views.paypal_success, name='paypal_success'),
    path('paypal/cancel/', views.paypal_cancel, name='paypal_cancel'),
    
    # PayPal webhook
    path('webhooks/paypal/', views.paypal_webhook, name='paypal_webhook'),
    path('webhooks/paypal/test/', views.paypal_webhook_test, name='paypal_webhook_test'),
]
