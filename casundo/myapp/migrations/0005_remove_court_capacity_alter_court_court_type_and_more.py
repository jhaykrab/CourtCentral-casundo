# Generated by Django 5.1.4 on 2025-01-29 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_alter_reservation_team'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='court',
            name='capacity',
        ),
        migrations.AlterField(
            model_name='court',
            name='court_type',
            field=models.CharField(blank=True, choices=[('basketball', 'Basketball'), ('tennis', 'Tennis'), ('badminton', 'Badminton'), ('other', 'Other'), ('full_covered', 'Full Covered Court'), ('half_covered', 'Half Covered Court'), ('full_open', 'Full Open Court'), ('half_open', 'Half Open Court')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='court',
            name='description',
            field=models.CharField(blank=True, choices=[('basketball', 'Basketball'), ('volleyball', 'Volleyball'), ('tennis', 'Tennis'), ('badminton', 'Badminton'), ('futsal', 'Futsal'), ('other', 'Other')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=10),
        ),
    ]
