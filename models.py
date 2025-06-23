from django.db import models
from django.contrib.auth.models import User
import datetime
import json

DESTINATIONS = [
    ("paris", "Paris"),
    ("tokyo", "Tokyo"),
    ("nyc", "New York City"),
    ("rome", "Rome"),
    ("cairo", "Cairo"),
    ("london", "London"),
]

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100, choices=DESTINATIONS)
    start_date = models.DateField(default=datetime.date(2025, 1, 1))
    end_date = models.DateField(default=datetime.date(2025, 12, 31))
    group_size = models.IntegerField(default=1)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    selected_activities = models.JSONField(default=list, blank=True, null=True)  # Store as comma-separated text
    itinerary_data = models.JSONField(default=dict, blank=True, null=True)


    def __str__(self):
        return f"{self.name} - {self.destination}"

class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    cuisine_type = models.CharField(max_length=50)
    average_price_per_person = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

class Activity(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)  # e.g., 'paris'
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='reservations')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    special_requests = models.TextField(blank=True)
