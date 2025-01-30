from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

RESERVATION_STATUSES = (
    ('PENDING', 'Pending'),
    ('CONFIRMED', 'Confirmed'),
    ('CANCELLED', 'Cancelled'),
)

class Court(models.Model):

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
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name="reservations", null=True, blank=True)
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="reservations")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=RESERVATION_STATUSES, default=RESERVATION_STATUSES[0][0])

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


class Payment(models.Model):
    PARTIAL = 'Partial'
    FULL = 'Full'

    PAYMENT_STATUSES = [
        (PARTIAL, 'Partial'),
        (FULL, 'Full'),
    ]

    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name="payment")
    amount = models.FloatField()
    downpayment = models.FloatField(null=True, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUSES, default=PARTIAL)
    date_paid = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.downpayment and self.downpayment > self.amount:
            raise ValidationError('Downpayment cannot exceed the total amount.')

    @property
    def remaining_balance(self):
        return max(0, self.amount - (self.downpayment or 0))

    def __str__(self):
        return f"Payment for {self.reservation} - {self.payment_status}"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"


class UserProfile(models.Model):
    ADMIN = 'Admin'
    OFFICER = 'Officer'
    USER = 'User'

    ROLES = [
        (ADMIN, 'Admin'),
        (OFFICER, 'Officer'),
        (USER, 'User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default=USER)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"