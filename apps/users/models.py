from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

class User(AbstractUser):
    # AbstractUser already has: username, first_name, last_name, email, password,
    # is_active, is_staff, is_superuser, last_login, date_joined
    phone = models.CharField(max_length=30, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    locale = models.CharField(max_length=10, default="fr")
    timezone = models.CharField(max_length=50, default="Africa/Casablanca")

    class Meta:
        constraints = [
            # Case-insensitive unique email on Postgres
            UniqueConstraint(Lower("email"), name="users_email_ci_unique", condition=~models.Q(email=""))
        ]

    def __str__(self):
        return self.username or self.email
