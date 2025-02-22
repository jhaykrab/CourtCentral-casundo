from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import (
    home, register_court, list_courts, create_reservation,
    court_calendar, calendar_reservations, update_team, delete_team,
    edit_reservation, delete_reservation, login_view, signup_view, 
    logout_view, reservation_status, get_reservation_details, update_reservation_status, get_reservation
)


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('load-auth-form/<str:mode>/', views.load_auth_form, name='load_auth_form'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('register_court/', views.register_court, name='register_court'),
    path('list_courts/', views.list_courts, name='list_courts'),
    path('edit_court_form/<int:court_id>/', views.edit_court_form, name='edit_court_form'),
    path('edit_court/<int:court_id>/', views.edit_court, name='edit_court'),  # <int:court_id> is important
    path('delete_court/<int:court_id>/', views.delete_court, name='delete_court'),  # <int:court_id> is important
    path('create_reservation/', views.create_reservation, name='create_reservation'),
    path('get_team_details/<int:team_id>/', views.get_team_details, name='get_team_details'),
    path("update_team/<int:team_id>/", update_team, name="update_team"),
    path('create_team/', views.create_team, name='create_team'),
    path("delete_team/<int:team_id>/", delete_team, name="delete_team"),
    path('court_calendar/', views.court_calendar, name='court_calendar'), # This is the correct line now
    path('calendar/reservations/', views.calendar_reservations, name='calendar_reservations'),  # Corrected name
    path('get_reservation/<int:reservation_id>/', get_reservation, name='get_reservation'),
    path('get_reservation_details/<int:reservation_id>/', views.get_reservation_details, name='get_reservation_details'),
    path('edit_reservation/<int:reservation_id>/', views.edit_reservation, name='edit_reservation'),
    path('delete_reservation/<int:reservation_id>/', views.delete_reservation, name='delete_reservation'),
    path('reservation-status/', views.reservation_status, name='reservation_status'),
    path('update_reservation_status/<int:reservation_id>/', update_reservation_status, name='update_reservation_status'),
    path('edit_reservation_page/<int:reservation_id>/', views.edit_reservation_page, name='edit_reservation_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)