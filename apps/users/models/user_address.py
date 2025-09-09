from django.db import models
from django.conf import settings

class UserAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey("users.Address", on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)
    label = models.CharField(max_length=50, blank=True, help_text="Custom label like 'Home', 'Work', etc.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [["user", "address"]]
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.address}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)