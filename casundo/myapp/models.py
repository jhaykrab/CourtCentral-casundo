from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone  



RESERVATION_STATUSES = (
    ('PENDING', 'Pending'),
    ('CONFIRMED', 'Confirmed'),
    ('CANCELLED', 'Cancelled'),
)

def get_default_user():
    from django.contrib.auth.models import User
    return User.objects.first().id if User.objects.exists() else None


class Court(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='courts',
        default=get_default_user
    )

    COURT_TYPES = (  # Tuple, not a list
        ('FULL_COVERED', 'Full Covered Court'),
        ('HALF_COVERED', 'Half Covered Court'),
        ('FULL_OPEN', 'Full Open Court'),
        ('HALF_OPEN', 'Half Open Court'),
        ('OTHER', 'Other'),
    )

    DESCRIPTION_CHOICES = (  # Tuple, not a list
        ('BASKETBALL', 'Basketball'),
        ('VOLLEYBALL', 'Volleyball'),
        ('TENNIS', 'Tennis'),
        ('BADMINTON', 'Badminton'),
        ('FUTSAL', 'Futsal'),
        ('OTHER', 'Other'),
    )

    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True, blank=True)
    court_type = models.CharField(max_length=50, choices=COURT_TYPES, null=True, blank=True)
    description = models.CharField(max_length=50, choices=DESCRIPTION_CHOICES, null=True, blank=True)
    image = models.ImageField(upload_to='courts/', null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Court"
        verbose_name_plural = "Courts"


class Team(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='teams',
        default=get_default_user
    )
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)

    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=15)
    

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"


class Reservation(models.Model):
    # Move choices to the top of the class
    COURT_STATUS_CHOICES = [
        ('UNUSED', 'Unused'),
        ('ONGOING', 'Ongoing'),
        ('DONE', 'Done'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations', default=get_default_user)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name="reservations", null=True, blank=True)
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="reservations")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=RESERVATION_STATUSES, default=RESERVATION_STATUSES[0][0])
    court_status = models.CharField(max_length=10, choices=COURT_STATUS_CHOICES, default='UNUSED')

    # Rest of the class remains the same
    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        overlaps = Reservation.objects.filter(
            court=self.court,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk if self.pk else None)
        if overlaps.exists():
            raise ValidationError('This court is already booked for this time.')
        super().clean()

    def __str__(self):
        return f"{self.team.name if self.team else 'No Team'} reserved {self.court.name} on {self.date} from {self.start_time} to {self.end_time}"

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['date', 'start_time']


class ReservationStatus(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PARTIAL', 'Partially Paid'),
        ('FULL', 'Fully Paid'),
    ]
    
    COURT_STATUS_CHOICES = [
        ('UNUSED', 'Unused'),
        ('ONGOING', 'Ongoing'),
        ('DONE', 'Done'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservation_statuses')
    # Update the related_name to avoid conflict
    reservation = models.OneToOneField(
        'Reservation', 
        on_delete=models.CASCADE, 
        related_name='reservation_status'  # Changed from 'status' to 'reservation_status'
    )
    amount = models.FloatField()
    downpayment = models.FloatField(null=True, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PARTIAL')
    court_status = models.CharField(max_length=10, choices=COURT_STATUS_CHOICES, default='UNUSED')
    date_updated = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.downpayment and self.downpayment > self.amount:
            raise ValidationError('Downpayment cannot exceed the total amount.')

    @property
    def remaining_balance(self):
        return max(0, self.amount - (self.downpayment or 0))

    def __str__(self):
        return f"Status for {self.reservation} - Payment: {self.payment_status}, Court: {self.court_status}"

    class Meta:
        verbose_name = "Reservation Status"
        verbose_name_plural = "Reservation Statuses"
        

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)  # This will work now
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'myapp_userprofile'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @classmethod
    def get_or_create_profile(cls, user, **profile_data):
        """Get or create a UserProfile for the given user with optional profile data."""
        profile, created = cls.objects.get_or_create(user=user)
        
        # Update profile with provided data
        if profile_data:
            for key, value in profile_data.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
            profile.save()
            
        return profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is created/updated."""
    UserProfile.get_or_create_profile(instance)