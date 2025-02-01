from django.core.management.base import BaseCommand
from myapp.models import Reservation, ReservationStatus

class Command(BaseCommand):
    help = 'Creates missing reservation statuses for existing reservations'

    def handle(self, *args, **kwargs):
        reservations = Reservation.objects.filter(reservation_status__isnull=True)
        count = 0
        for reservation in reservations:
            ReservationStatus.objects.create(
                user=reservation.user,
                reservation=reservation,
                amount=400,  # Default amount
                payment_status='PARTIAL',
                court_status='UNUSED'
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {count} reservation statuses'))