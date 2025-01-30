from django import forms
from .models import Court, Reservation, Team

COURT_TYPE_CHOICES = (
    ('FULL_COVERED', 'Full Covered Court'),
    ('HALF_COVERED', 'Half Covered Court'),
    ('FULL_OPEN', 'Full Open Court'),
    ('HALF_OPEN', 'Half Open Court'),
    ('OTHER', 'Other'),
)

DESCRIPTION_CHOICES = (  # Choices for the description field
    ('BASKETBALL', 'Basketball'),
    ('VOLLEYBALL', 'Volleyball'),
    ('TENNIS', 'Tennis'),
    ('BADMINTON', 'Badminton'),
    ('FUTSAL', 'Futsal'),  # Example, add more as needed
    ('OTHER', 'Other'),
)

class CourtForm(forms.ModelForm):
    court_type = forms.ChoiceField(choices=COURT_TYPE_CHOICES, widget=forms.RadioSelect)
    description = forms.ChoiceField(choices=DESCRIPTION_CHOICES, widget=forms.RadioSelect) # Add the description field
    image = forms.ImageField(required=False)

    class Meta:
        model = Court
        fields = ['name', 'location', 'court_type', 'description', 'image']  # Include description
        labels = {
            'name': 'Court Name',
            'location': 'Location',
            'court_type': 'Court Type',
            'description': 'Description',  # Label for description
            'image': 'Court Image',
        }
        help_texts = {
            'name': 'Enter the name of the court.',
            'location': 'Enter the location of the court.',
            'court_type': 'Select the type of court.',
            'description': 'Select the type of court activity.', # Help text for description
            'image': 'Upload an image of the court (optional).',
        }



class ReservationForm(forms.ModelForm):
    team = forms.ModelChoiceField(queryset=Team.objects.all(), required=True, label="Team")

    class Meta:
        model = Reservation
        fields = ['court', 'team', 'date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        court = cleaned_data.get('court')
        team = cleaned_data.get('team')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Start time must be before end time.")

        if court and date and start_time and end_time:
            overlapping_reservations = Reservation.objects.filter(
                court=court,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(pk=self.instance.pk if self.instance else None)
            if overlapping_reservations.exists():
                raise forms.ValidationError("This time slot is already booked.")

        if not team:
            raise forms.ValidationError("Team is required")

        return cleaned_data