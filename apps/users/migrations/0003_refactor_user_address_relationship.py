# Generated manually for refactoring User-Address relationship
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_address_useraddress_user_addresses_and_more'),
    ]

    operations = [
        # Step 1: Remove the ManyToMany relationship
        migrations.RemoveField(
            model_name='user',
            name='addresses',
        ),
        
        # Step 2: Add new fields to Address model
        migrations.AddField(
            model_name='address',
            name='user',
            field=models.ForeignKey(
                default=1,  # Temporary default - will be updated in data migration
                on_delete=django.db.models.deletion.CASCADE,
                related_name='addresses',
                to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='address',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='address',
            name='label',
            field=models.CharField(
                blank=True,
                help_text="Custom label like 'Home', 'Work', etc.",
                max_length=50
            ),
        ),
        
        # Step 3: Update indexes
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['user', 'is_default'], name='users_address_user_is_default_idx'),
        ),
        
        # Step 4: Remove UserAddress model (after step 5 data migration)
        migrations.DeleteModel(
            name='UserAddress',
        ),
    ]