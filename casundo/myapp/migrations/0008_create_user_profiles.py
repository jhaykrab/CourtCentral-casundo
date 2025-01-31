from django.db import migrations
from django.utils import timezone

def create_user_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('myapp', 'UserProfile')
    
    for user in User.objects.all():
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_user_profiles),
    ]