import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import Trip, Hotel, Restaurant, Activity, Reservation
from .Itinerary import create_itinerary_with_messages
from datetime import datetime
from datetime import timedelta

def welcome_view(request):
    return render(request, 'trips/welcome.html')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/dashboard/'

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'trips/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('welcome')

@login_required
def dashboard_view(request):
    trip = Trip.objects.filter(user=request.user).first()
    return render(request, 'trips/dashboard.html', {'trip': trip})

@login_required
def trip_details_view(request):
    if request.method == 'POST':
        request.session['trip_details'] = {
            'name': request.POST.get('name'),
            'destination': request.POST.get('destination'),
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date'),
            'group_size': request.POST.get('group_size'),
            'budget': request.POST.get('budget')
        }
        return redirect('select_hotel')
    return render(request, 'trips/trip_details.html')

@login_required
def hotel_selection_view(request):
    trip_details = request.session.get('trip_details')
    if not trip_details:
        return redirect('trip_details')

    destination = trip_details.get('destination')
    hotels = Hotel.objects.filter(location__iexact=destination)

    banner_map = {
        "paris": "bg_paris.jpg",
        "london": "bg_paris.jpg",
        "tokyo": "bg_tokyo.jpg",
        "cairo": "bg_cairo.jpg",
        "nyc": "bg_nyc.jpg"
    }
    banner = f"trips/images/{banner_map.get(destination.lower(), 'bg_dashboard.jpg')}"

    if request.method == 'POST':
        selected_hotel_id = request.POST.get('hotel_id')
        request.session['selected_hotel'] = selected_hotel_id
        hotel = Hotel.objects.get(id=selected_hotel_id)
        group_size = int(trip_details['group_size'])
        start_date = datetime.strptime(trip_details['start_date'], "%m-%d-%Y")
        end_date = datetime.strptime(trip_details['end_date'], "%m-%d-%Y")

        nights = (end_date - start_date).days
        cost = float(hotel.price_per_night) * group_size * nights
        request.session['trip_budget_remaining'] = float(trip_details['budget']) - cost
        return redirect('select_restaurants')

    return render(request, 'trips/hotel_selection.html', {
        'hotels': hotels,
        'destination': destination,
        'banner': banner
    })

@login_required
def restaurant_selection_view(request):
    trip_details = request.session.get('trip_details')
    if not trip_details:
        return redirect('trip_details')

    destination = trip_details['destination']
    group_size = int(trip_details['group_size'])
    restaurants = Restaurant.objects.filter(location__iexact=destination)

    banner_map = {
        "paris": "bg_paris.jpg",
        "london": "bg_paris.jpg",
        "tokyo": "bg_tokyo.jpg",
        "cairo": "bg_cairo.jpg",
        "nyc": "bg_nyc.jpg"
    }
    banner = f"trips/images/{banner_map.get(destination.lower(), 'bg_dashboard.jpg')}"

    if request.method == 'POST':
        selected_ids = request.POST.getlist('restaurant_id')
        request.session['selected_restaurants'] = selected_ids

        reservation_details = {}
        for rid in selected_ids:
            reservation_details[rid] = {
                "reservation_date": request.POST.get(f'reservation_date_{rid}'),
                "reservation_time": request.POST.get(f'reservation_time_{rid}'),
                "special_requests": request.POST.get(f'special_requests_{rid}')
            }

        request.session['reservation_details'] = reservation_details

        total = sum(float(Restaurant.objects.get(id=id).average_price_per_person) for id in selected_ids)
        total_cost = total * group_size
        request.session['trip_budget_remaining'] = float(request.session['trip_budget_remaining']) - total_cost

        return redirect('select_activities')

    return render(request, 'trips/restaurant_selection.html', {
        'restaurants': restaurants,
        'banner': banner,
        'destination': destination
    })

@login_required
def activity_selection_view(request):
    trip_details = request.session.get('trip_details')
    if not trip_details:
        return redirect('trip_details')

    destination = trip_details['destination']
    trip_name = trip_details['name']
    banner_map = {
        "paris": "trips/images/bg_paris.jpg",
        "london": "trips/images/bg_london.jpg",
        "tokyo": "trips/images/bg_tokyo.jpg",
        "cairo": "trips/images/bg_cairo.jpg",
        "nyc": "trips/images/bg_nyc.jpg"
    }
    banner = banner_map.get(destination.lower(), "trips/images/bg_dashboard.jpg")

    if request.method == "POST":
        selected = request.POST.getlist("activities")
        print("Selected activities from form:", selected)  # Debug: Check what's being selected
        request.session['selected_activities'] = selected  # Save activities in session
        print("Activities stored in session:", request.session.get('selected_activities'))
        return redirect('itinerary')

    return render(request, 'trips/activities.html', {
        'trip_name': trip_name,
        'destination': destination,
        'banner': banner
    })

@login_required
def itinerary_view(request):
    trip_details = request.session.get('trip_details')
    selected_activities = request.session.get('selected_activities')
    selected_hotel_id = request.session.get('selected_hotel')
    selected_restaurant_ids = request.session.get('selected_restaurants', [])

    start_date = datetime.strptime(trip_details['start_date'], "%m-%d-%Y")
    end_date = datetime.strptime(trip_details['end_date'], "%m-%d-%Y")
    num_days = (end_date - start_date).days + 1
    city = trip_details['destination']
    group_size = int(trip_details.get('group_size', 1))
    total_budget = float(trip_details.get('budget', 0))

    banner_map = {
        "paris": "trips/images/bg_paris.jpg",
        "london": "trips/images/bg_london.jpg",
        "tokyo": "trips/images/bg_tokyo.jpg",
        "cairo": "trips/images/bg_cairo.jpg",
        "nyc": "trips/images/bg_nyc.jpg"
    }
    banner = banner_map.get(city.lower(), "trips/images/bg_dashboard.jpg")

    hotel = Hotel.objects.get(id=selected_hotel_id)
    hotel_cost = float(hotel.price_per_night) * num_days * group_size

    restaurants = Restaurant.objects.filter(id__in=selected_restaurant_ids)
    restaurant_cost = sum([float(r.average_price_per_person) for r in restaurants]) * group_size

    if isinstance(selected_activities, str):
        selected_activities = selected_activities.split(",")
        

    detailed_itinerary = create_itinerary_with_messages(selected_activities, num_days, city, shuffle=True)
    request.session['final_itinerary'] = detailed_itinerary

    # Calculates cost of activity, scaled with group size, and subtracts it from the remaining balance
    activity_cost = sum(float(act.get("RawCost", 0)) * group_size for day in detailed_itinerary.values() for act in day)
    remaining_budget = total_budget - (hotel_cost + restaurant_cost + activity_cost)

    return render(request, 'trips/itinerary.html', {
        'itinerary': detailed_itinerary,
        'trip_name': trip_details['name'],
        'destination': city.title(),
        'banner': banner,
        'budget_summary': {
            'total_budget': f"${total_budget:,.2f}",
            'hotel_cost': f"${hotel_cost:,.2f}",
            'restaurant_cost': f"${restaurant_cost:,.2f}",
            'activity_cost': f"${activity_cost:,.2f}",
            'remaining_budget': f"${remaining_budget:,.2f}"
        }
    })

@login_required
def trip_summary_view(request):
    trip_details = request.session.get('trip_details')
    selected_hotel_id = request.session.get('selected_hotel')
    selected_restaurant_ids = request.session.get('selected_restaurants', [])
    selected_activities = request.session.get('selected_activities', [])

    if isinstance(selected_activities, str):
        selected_activities = selected_activities.split(",")

    print("Selected Activities before itinerary generation:", selected_activities)

    start_date = datetime.strptime(trip_details['start_date'], "%m-%d-%Y")
    end_date = datetime.strptime(trip_details['end_date'], "%m-%d-%Y")
    num_days = (end_date - start_date).days + 1
    city = trip_details['destination']
    group_size = int(trip_details.get('group_size', 1))
    total_budget = float(trip_details.get('budget', 0))



    hotel = Hotel.objects.get(id=selected_hotel_id)
    hotel_cost = float(hotel.price_per_night) * num_days * group_size

    restaurants = Restaurant.objects.filter(id__in=selected_restaurant_ids)
    restaurant_cost = sum([float(r.average_price_per_person) for r in restaurants]) * group_size



    itinerary = request.session.get('final_itinerary')
    activity_cost = sum(float(act.get("RawCost", 0)) * group_size for day in itinerary.values() for act in day)
    remaining_budget = total_budget - (hotel_cost + restaurant_cost + activity_cost)

    banner_map = {
        "paris": "trips/images/bg_paris.jpg",
        "london": "trips/images/bg_london.jpg",
        "tokyo": "trips/images/bg_tokyo.jpg",
        "cairo": "trips/images/bg_cairo.jpg",
        "nyc": "trips/images/bg_nyc.jpg"
    }
    banner = banner_map.get(city.lower(), "trips/images/bg_dashboard.jpg")

    if request.method == 'POST':
        trip = Trip.objects.create(
            user=request.user,
            name=trip_details['name'],
            destination=city,
            start_date=start_date,
            end_date=end_date,
            group_size=group_size,
            budget=total_budget,
            selected_activities=",".join(selected_activities)
        )

        # Save the final itinerary (from session) to the trip record
        itinerary = request.session.get('final_itinerary')
        trip.itinerary_data = itinerary
        trip.save()


        reservation_data = request.session.get('reservation_details', {})
        for restaurant_id, details in reservation_data.items():
            if str(restaurant_id) == "special_requests":
                continue
            Reservation.objects.create(
                trip=trip,
                restaurant_id=int(restaurant_id),
                reservation_date=details.get("reservation_date"),
                reservation_time=details.get("reservation_time"),
                special_requests=details.get("special_requests", "")
            )

        return redirect('dashboard')

    return render(request, 'trips/trip_summary.html', {
        'trip': trip_details,
        'hotel': hotel,
        'restaurants': restaurants,
        'activities': selected_activities,
        'itinerary': itinerary,
        'banner': banner,
        'reservation_data': request.session.get('reservation_details', {}),
        'budget_summary': {
            'total_budget': f"${total_budget:,.2f}",
            'hotel_cost': f"${hotel_cost:,.2f}",
            'restaurant_cost': f"${restaurant_cost:,.2f}",
            'activity_cost': f"${activity_cost:,.2f}",
            'remaining_budget': f"${remaining_budget:,.2f}"
        },
        'over_budget': remaining_budget < 0
    })



@login_required
def view_saved_trips(request):
    trips = Trip.objects.filter(user=request.user)
    return render(request, 'trips/saved_trips.html', {'trips': trips})

@login_required
def view_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    
    start_date = trip.start_date
    end_date = trip.end_date
    num_days = (end_date - start_date).days + 1
    group_size = trip.group_size
    destination = trip.destination
    total_budget = float(trip.budget)

    hotel = Hotel.objects.filter(location__iexact=destination).first()
    hotel_cost = float(hotel.price_per_night) * group_size * num_days if hotel else 0

    reservations = Reservation.objects.filter(trip=trip)
    restaurant_ids = [res.restaurant.id for res in reservations]
    restaurants = Restaurant.objects.filter(id__in=restaurant_ids)
    restaurant_cost = sum([float(r.average_price_per_person) for r in restaurants]) * group_size

    selected_activities = trip.selected_activities.split(",") if trip.selected_activities else []
    itinerary = trip.itinerary_data


    activity_cost = 0
    for day, activities in itinerary.items():
        for activity in activities:
            raw = activity.get("RawCost")
            if raw:
                activity_cost += float(raw) * group_size


    remaining_budget = total_budget - (hotel_cost + restaurant_cost + activity_cost)

    banner_map = {
        "paris": "trips/images/bg_paris.jpg",
        "london": "trips/images/bg_london.jpg",
        "tokyo": "trips/images/bg_tokyo.jpg",
        "cairo": "trips/images/bg_cairo.jpg",
        "nyc": "trips/images/bg_nyc.jpg"
    }
    banner = banner_map.get(destination.lower(), "trips/images/bg_dashboard.jpg")

    context = {
        'trip': trip,
        'hotel': hotel,
        'restaurants': restaurants,
        'reservations': reservations,
        'itinerary': itinerary,
        'banner': banner,
        'budget_summary': {
            'total_budget': f"${total_budget:,.2f}",
            'hotel_cost': f"${hotel_cost:,.2f}",
            'restaurant_cost': f"${restaurant_cost:,.2f}",
            'activity_cost': f"${activity_cost:,.2f}",
            'remaining_budget': f"${remaining_budget:,.2f}"
        }
    }

    return render(request, 'trips/view_trip.html', context)


@login_required
def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    trip.delete()
    return redirect('view_saved_trips')
