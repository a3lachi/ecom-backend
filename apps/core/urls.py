from django.urls import path
from .views import HealthCheckView, MigrateView, CreateSuperuserView, DatabaseDebugView

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health-check'),
    path('migrate/', MigrateView.as_view(), name='migrate'),
    path('create-superuser/', CreateSuperuserView.as_view(), name='create-superuser'),
    path('debug-db/', DatabaseDebugView.as_view(), name='debug-database'),
]