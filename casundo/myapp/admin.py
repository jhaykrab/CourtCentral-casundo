from django.contrib import admin
from .models import Court, Reservation, ReservationStatus, Team, UserProfile

# Register models
admin.site.register(Court)
admin.site.register(Reservation)
admin.site.register(ReservationStatus)
admin.site.register(Team)
admin.site.register(UserProfile)
