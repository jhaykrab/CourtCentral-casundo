from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.template.loader import render_to_string
from .models import Court, Reservation, Team, UserProfile, ReservationStatus
from .forms import ReservationForm, CourtForm, SignUpForm
from django.core.exceptions import ValidationError
from django.utils import timezone 
from datetime import datetime

import json
import logging

logger = logging.getLogger(__name__)



@ensure_csrf_cookie
def home(request):
    return render(request, 'myApp/home.html')

@ensure_csrf_cookie
def load_auth_form(request, mode):
    return render(request, 'myApp/auth_form.html', {'mode': mode})


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        
        # Try to authenticate with username
        user = authenticate(username=username_or_email, password=password)
        
        # If authentication failed, try with email
        if user is None:
            try:
                user = User.objects.get(email=username_or_email)
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('home')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'Invalid credentials. Please try again.'
                })
            # Handle regular form submission error
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'myApp/login.html', {'mode': 'login'})
    
    return render(request, 'myApp/login.html', {'mode': 'login'})

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = user.profile
            
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            
            if current_password and new_password:
                # Verify current password
                if not user.check_password(current_password):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Current password is incorrect'
                    }, status=400)
                
                # Set new password
                user.set_password(new_password)
            
            # Update user fields
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.save()
            
            # Update profile fields
            profile.phone_number = request.POST.get('phone_number')
            profile.address = request.POST.get('address')
            
            # Handle profile picture
            if request.FILES.get('profile_picture'):
                profile.profile_picture = request.FILES['profile_picture']
            
            profile.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Profile updated successfully',
                'username': user.username
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_protect
def signup_view(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username_or_email')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        profile_picture = request.FILES.get('profile_picture')

        try:
            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return render(request, 'myApp/login.html', {'mode': 'signup'})
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'myApp/login.html', {'mode': 'signup'})

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Create or update profile with the provided data
            UserProfile.get_or_create_profile(
                user,
                phone_number=phone_number,
                address=address,
                profile_picture=profile_picture,
                created_at=timezone.now()
            )

            # Log the user in
            login(request, user)

            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            # Redirect to home page for normal request
            messages.success(request, 'Account created successfully!')
            return redirect('home')

        except Exception as e:
            # If there was an error, delete the user if it was created
            if 'user' in locals():
                user.delete()
            
            messages.error(request, str(e))
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
            return render(request, 'myApp/login.html', {'mode': 'signup'})

    # If GET request, show signup form
    return render(request, 'myApp/login.html', {'mode': 'signup'})

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
            court = form.save(commit=False)
            court.user = request.user
            court.save()
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
    courts = Court.objects.filter(user=request.user)
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
    court = get_object_or_404(Court, pk=court_id, user=request.user)
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
            court = get_object_or_404(Court, pk=court_id, user=request.user) 
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
        team = Team.objects.get(pk=team_id, user=request.user)
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
@login_required
def create_reservation(request):
    teams = Team.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        selected_team_id = request.POST.get('team')

        if form.is_valid():
            try:
                # Get the team instance
                team = get_object_or_404(Team, pk=selected_team_id)
                
                # Create reservation instance but don't save yet
                reservation = form.save(commit=False)
                reservation.user = request.user
                reservation.team = team

                # Generate reservation number (TEAM4DIGITS + MMDDYYYY)
                team_prefix = team.name[:4].upper()
                date_suffix = datetime.now().strftime('%m%d%Y')
                reservation.reservation_number = f"{team_prefix}{date_suffix}"

                # Save the reservation
                reservation.save()

                # Create payment record
                payment = ReservationStatus.objects.create(
                    user=request.user,
                    reservation=reservation,
                    amount=form.cleaned_data['payment_amount'],
                    downpayment=form.cleaned_data.get('downpayment'),
                    payment_status='PARTIAL' if form.cleaned_data['payment_type'] == 'INSTALLMENT' else 'FULL'
                )

                messages.success(
                    request,
                    f"Reservation created successfully! Your reservation number is: {reservation.reservation_number}"
                )
                


            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error creating reservation: {str(e)}'
                }, status=400)
        else:
            # Get all error messages and join them
            error_messages = []
            for field, errors in form.errors.items():
                if field == '__all__':  # Non-field errors
                    error_messages.extend([str(error) for error in errors])
                else:
                    error_messages.extend([f"{field}: {str(error)}" for error in errors])
            
            return JsonResponse({
                'status': 'error',
                'message': " ".join(error_messages)
            }, status=400)
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
    search_query = request.GET.get('search', '').strip().upper()
    selected_date = None
    reservations = []

    # Base queryset with related data
    base_query = Reservation.objects.filter(user=request.user).select_related('team', 'court')

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            reservations = base_query.filter(date=selected_date)
        except ValueError:
            pass

    # Apply search filter if there's a search query
    if search_query:
        reservations = base_query.filter(
            reservation_number__exact=search_query
        )

    courts = Court.objects.filter(user=request.user).prefetch_related('reservations')
    teams = Team.objects.filter(user=request.user)

    return render(request, 'myApp/court_calendar.html', {
        'reservations': reservations,
        'selected_date': selected_date,
        'courts': courts,
        'teams': teams,
        'search_query': search_query,  # Pass search query to template
    })

@login_required
def get_reservation_details(request, reservation_id):
    try:
        reservation = get_object_or_404(
            Reservation.objects.select_related('reservation_status', 'team', 'court'),
            id=reservation_id,
            user=request.user
        )
        
        # Create reservation status if it doesn't exist
        if not hasattr(reservation, 'reservation_status'):
            reservation_status = ReservationStatus.objects.create(
                user=reservation.user,
                reservation=reservation,
                amount=400,
                payment_status='PARTIAL',
                court_status='UNUSED'
            )
        else:
            reservation_status = reservation.reservation_status

        data = {
            'status': 'success',
            'reservation': {
                'reservation_number': reservation.reservation_number,  # Add this line
                'date': reservation.date,
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'court_status': reservation.reservation_status.court_status if reservation.reservation_status else 'UNUSED',
            },
            'team': {
                'id': reservation.team.id if reservation.team else None,
                'name': reservation.team.name if reservation.team else 'No Team',
                'contact_person': reservation.team.contact_person if reservation.team else '',
                'contact_email': reservation.team.contact_email if reservation.team else '',
                'contact_phone': reservation.team.contact_phone if reservation.team else ''
            },
            'court': {
                'id': reservation.court.id,
                'name': reservation.court.name,
                'location': reservation.court.location if hasattr(reservation.court, 'location') else '',
                'description': reservation.court.description if hasattr(reservation.court, 'description') else ''
            },
            'payment': {
                'status': reservation_status.payment_status,
                'amount': str(reservation_status.amount),
                'downpayment': str(reservation_status.downpayment) if reservation_status.downpayment else None,
                'balance': str(reservation_status.amount - (reservation_status.downpayment or 0))
            }
        }
        print("Data being sent:", data)  # For debugging
        return JsonResponse(data)
    except Exception as e:
        print(f"Error in get_reservation_details: {str(e)}")  # For debugging
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def get_reservation(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        data = {
            'status': 'success',
            'reservation': {
                'team_id': reservation.team.id if reservation.team else None,
                'court_id': reservation.court.id,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def update_reservation_status(request, reservation_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
            
            if data['status_type'] == 'payment':
                payment = reservation.payment
                payment.payment_status = data['status']
                payment.save()
            elif data['status_type'] == 'court':
                reservation.court_status = data['status']
                reservation.save()
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@login_required
def edit_reservation_page(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        teams = Team.objects.filter(user=request.user)
        courts = Court.objects.filter(user=request.user)

        context = {
            'reservation': reservation,
            'teams': teams,
            'courts': courts,
        }
        return render(request, 'myApp/edit_reservation.html', context)
    except Exception as e:
        messages.error(request, f'Error loading reservation: {str(e)}')
        return redirect('reservation_status')
    
@csrf_exempt
@login_required
def edit_reservation(request, reservation_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
            reservation_status = reservation.reservation_status  # Updated from status to reservation_status
            
            # Update both statuses
            if data.get('payment_status'):
                reservation_status.payment_status = data['payment_status']
            if data.get('court_status'):
                reservation_status.court_status = data['court_status']
            
            reservation_status.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Status updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_reservation(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        reservation.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Reservation deleted successfully'
        })
    except Exception as e:
        print(f"Error deleting reservation: {str(e)}")  # For debugging
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def reservation_status(request):
    # Get the search query from request
    search_query = request.GET.get('search', '').strip().upper()  # Convert to uppercase since reservation numbers are stored uppercase
    
    # Base queryset with related data
    reservations = Reservation.objects.select_related(
        'user', 
        'team', 
        'court', 
        'reservation_status'
    ).filter(user=request.user)
    
    # Apply search filter if there's a search query
    if search_query:
        reservations = reservations.filter(
            reservation_number__exact=search_query  # Use exact match instead of icontains
        )
    
    # Order by date
    reservations = reservations.order_by('-date')

    # Create missing reservation statuses if needed
    for reservation in reservations:
        if not hasattr(reservation, 'reservation_status'):
            ReservationStatus.objects.create(
                user=reservation.user,
                reservation=reservation,
                amount=400,  # Default amount
                downpayment=0,  # Default downpayment
                payment_status='PARTIAL',
                court_status='UNUSED'
            )

    context = {
        'reservations': reservations,
        'search_query': search_query,  # Pass the search query back to the template
    }
    return render(request, 'myApp/reservation_status.html', context)


@login_required
def calendar_reservations(request):
    try:
        reservations = Reservation.objects.filter(
            user=request.user
        ).select_related('team', 'court')
        
        events = []
        for reservation in reservations:
            event = {
                'id': reservation.id,
                'title': f"{reservation.reservation_number} - {reservation.team.name if reservation.team else 'No Team'} ({reservation.court.name})",
                'start': f"{reservation.date.isoformat()}T{reservation.start_time.strftime('%H:%M:%S')}",
                'end': f"{reservation.date.isoformat()}T{reservation.end_time.strftime('%H:%M:%S')}",
                'description': reservation.court.description,
                'court_id': reservation.court.id,
                'court_name': reservation.court.name,
                'team_id': reservation.team.id if reservation.team else None,
                'team_name': reservation.team.name if reservation.team else 'No Team',
                'reservation_number': reservation.reservation_number
            }
            events.append(event)

        return JsonResponse(events, safe=False)
    except Exception as e:
        logger.error(f"Error in calendar_reservations: {e}")
        return JsonResponse({'error': str(e)}, status=500)

