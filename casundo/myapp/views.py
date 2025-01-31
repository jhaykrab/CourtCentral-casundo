from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.template.loader import render_to_string
from .models import Court, Reservation, Team, UserProfile
from .forms import ReservationForm, CourtForm, SignUpForm
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'myApp/home.html')


@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')  # Updated field name
        password = request.POST.get('password')

        # Check if the input is an email
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                username = None
        else:
            username = username_or_email

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'myApp/login.html', {
        'mode': 'login',
        'hide_navbar': True  # Add this line
    })

@csrf_protect
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            # Get form data
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'myApp/login.html', {'form': form, 'mode': 'signup'})
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'myApp/login.html', {'form': form, 'mode': 'signup'})
            
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Update profile
                profile = user.profile
                profile.phone_number = form.cleaned_data.get('phone_number')
                profile.address = form.cleaned_data.get('address')
                if form.cleaned_data.get('profile_picture'):
                    profile.profile_picture = form.cleaned_data['profile_picture']
                profile.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('home')
                
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return render(request, 'myApp/login.html', {'form': form, 'mode': 'signup'})
    else:
        form = SignUpForm()
        
        return render(request, 'myApp/login.html', {
            'form': form,
            'mode': 'signup',
            'hide_navbar': True  # Add this line
        })

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('login')



@login_required
def register_court(request):
    if request.method == 'POST':
        form = CourtForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Court registered successfully!")
            return redirect('list_courts')
        else:
            print(form.errors)
            messages.error(request, "There were errors in the form. Please correct them.")  # More user-friendly message
    else:
        form = CourtForm()
    return render(request, 'myApp/register_court.html', {'form': form}) # edit_mode defaults to False, court is None

@login_required
def list_courts(request):
    courts = Court.objects.all()
    return render(request, 'myApp/list_courts.html', {'courts': courts})

@login_required
def edit_court_form(request, court_id):
    court = get_object_or_404(Court, pk=court_id)
    form = CourtForm(instance=court)
    form_html = render_to_string('myApp/court_form.html', {'form': form})
    print(form_html)  # Print the HTML to the console
    return JsonResponse({'form_html': form_html})

@login_required
def edit_court(request, court_id):
    court = get_object_or_404(Court, pk=court_id)
    if request.method == 'POST':
        print(f"Received POST data: {request.POST}")  # Debugging
        form = CourtForm(request.POST, request.FILES, instance=court)
        if form.is_valid():
            form.save()
            print("Court successfully updated!")  # Debugging
            return JsonResponse({'status': 'success', 'message': "Court updated successfully!"})
        else:
            print("Form errors:", form.errors)  # Debugging
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)


@login_required
@csrf_exempt
def delete_court(request, court_id):
    if request.method == 'DELETE':
        try:
            court = get_object_or_404(Court, pk=court_id)
            court.delete()
            messages.success(request, "Court deleted successfully!")
            return JsonResponse({'status': 'success'})
        except Court.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Court not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required
def get_team_details(request, team_id):
    try:
        team = Team.objects.get(pk=team_id)
        return JsonResponse({
            'name': team.name,
            'contact_person': team.contact_person,
            'contact_email': team.contact_email,
            'contact_phone': team.contact_phone
        })
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)

@login_required
@csrf_exempt
def create_team(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get('name')
            contact_person = data.get('contact_person')
            contact_email = data.get('contact_email')
            contact_phone = data.get('contact_phone')

            if not name or not contact_person or not contact_phone:
                return JsonResponse({'status': 'error', 'message': 'All required fields must be filled!'}, status=400)

            team = Team.objects.create(
                name=name,
                contact_person=contact_person,
                contact_email=contact_email,
                contact_phone=contact_phone
            )

            return JsonResponse({'status': 'success', 'team_id': team.id, 'team_name': team.name}, status=201)

        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Request Body: {request.body.decode('utf-8')}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
@csrf_exempt
def update_team(request, team_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            team = Team.objects.get(pk=team_id)

            team.name = data.get("name", team.name)
            team.contact_person = data.get("contact_person", team.contact_person)
            team.contact_email = data.get("contact_email", team.contact_email)
            team.contact_phone = data.get("contact_phone", team.contact_phone)
            team.save()

            return JsonResponse({"status": "success", "updated_team": {"name": team.name}})

        except Team.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Team not found"}, status=404)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Request Body: {request.body.decode('utf-8')}")
            return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
@csrf_exempt
def delete_team(request, team_id):
    if request.method == "DELETE":
        try:
            team = Team.objects.get(pk=team_id)
            team.delete()
            return JsonResponse({"status": "success"}, status=200)
        except Team.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Team not found"}, status=404)

@login_required
def create_reservation(request):
    teams = Team.objects.all()

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        selected_team_id = request.POST.get('team')

        if form.is_valid():
            reservation = form.save(commit=False)

            if selected_team_id:
                reservation.team = get_object_or_404(Team, pk=selected_team_id)

            reservation.save()
            messages.success(request, "Reservation created successfully!")
            return redirect(reverse('create_reservation'))
        else:
            messages.error(request, "There was an error with your reservation.")
            print(form.errors) # Print form errors for debugging
    else:
        form = ReservationForm()
        selected_team_id = None

    return render(request, 'myapp/create_reservation.html', {
        'form': form,
        'teams': teams,
        'selected_team_id': selected_team_id
    })

@login_required
def court_calendar(request):
    selected_date_str = request.GET.get('date')
    selected_date = None
    reservations = []

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            reservations = Reservation.objects.filter(date=selected_date).select_related('team', 'court')
        except ValueError:
            pass

    # Fetch all courts with their related reservations
    courts = Court.objects.prefetch_related('reservations').all()

    return render(request, 'myApp/court_calendar.html', {
        'reservations': reservations,
        'selected_date': selected_date,
        'courts': courts,  # Pass courts to the template
    })

@csrf_exempt
def get_reservation(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        data = {
            'status': 'success',
            'reservation': {
                'team_id': reservation.team.id,
                'court_id': reservation.court.id,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M:%S'),
                'end_time': reservation.end_time.strftime('%H:%M:%S'),
            }
        }
        return JsonResponse(data)
    except Reservation.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Reservation not found'}, status=404)

@login_required
@csrf_exempt
def edit_reservation(request, reservation_id):
    if request.method == 'POST':
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.team_id = request.POST.get('team')
            reservation.court_id = request.POST.get('court')
            reservation.date = request.POST.get('date')
            reservation.start_time = request.POST.get('start_time')
            reservation.end_time = request.POST.get('end_time')
            reservation.save()
            return JsonResponse({'status': 'success'})
        except Reservation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Reservation not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
@csrf_exempt
def delete_reservation(request, reservation_id):
    if request.method == 'DELETE':
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.delete()
            return JsonResponse({'status': 'success'})
        except Reservation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Reservation not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def calendar_reservations(request):
    try:
        reservations = Reservation.objects.select_related('team', 'court')
        events = []

        for reservation in reservations:
            events.append({
                'id': reservation.id,  # Include the reservation ID
                'title': f"{reservation.team.name if reservation.team else 'No Team'} ({reservation.court.name if reservation.court else 'No Court'})",
                'start': reservation.date.isoformat() + 'T' + reservation.start_time.strftime('%H:%M:%S'),
                'end': reservation.date.isoformat() + 'T' + reservation.end_time.strftime('%H:%M:%S'),
                'description': reservation.court.description if reservation.court else 'No Description',
                'court_name': reservation.court.name if reservation.court else 'No Court',
                'team_name': reservation.team.name if reservation.team else 'No Team',
            })

        logger.debug(f"Events data: {events}")  # Log the events data
        return JsonResponse(events, safe=False)
    except Exception as e:
        logger.error(f"Error in calendar_reservations: {e}")
        return JsonResponse({'error': str(e)}, status=500)
