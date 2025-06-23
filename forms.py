from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Trip
from .Activities import available_activities


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TripForm(forms.ModelForm):
    activities = forms.MultipleChoiceField(
        choices=[(activity, activity) for activity in available_activities],
        widget=forms.CheckboxSelectMultiple,            # Uses checkboxes for activity selection
        label="Select up to 8 activities",
        required=True
    )

    # Creates field to allow user to enter how many days the trip lasts (Between 1 - 30 day limit)
    trip_duration = forms.IntegerField(
        min_value=1,
        max_value=30,
        label="How many days is your trip?"
    )

    # Allows user to enter their budget in dollars, will be used to compare against estimated trip cost
    total_budget = forms.DecimalField(
    label="Total Trip Budget ($)",
    min_value=0.00,
    max_digits=10,
    decimal_places=2,
    required=True
    )

    # Order of which the fields will be displayed on the form
    class Meta:
        model = Trip
        fields = ['name', 'destination', 'trip_duration', 'activities', 'total_budget']

    # Ensures that the user can only have 8 activities
    def clean_activities(self):
        selected = self.cleaned_data['activities']
        if len(selected) > 8:
            raise forms.ValidationError("You can only choose up to 8 activities.")
        return selected
