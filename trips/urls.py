from django.contrib import admin
from django.urls import path
from .views import (
    welcome_view,
    register_view,
    dashboard_view,
    trip_details_view,
    itinerary_view,
    logout_view,
    hotel_selection_view,
    activity_selection_view,
    restaurant_selection_view,
    trip_summary_view,
    view_saved_trips,
    view_trip,
    delete_trip,
    CustomLoginView
)

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', welcome_view, name='welcome'),
    path('admin/', admin.site.urls),
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('trip/details/', trip_details_view, name='trip_details'),
    path('trip/select-hotel/', hotel_selection_view, name='select_hotel'),
    path('trip/select-restaurants/', restaurant_selection_view, name='select_restaurants'),
    path('trip/activities/', activity_selection_view, name='select_activities'),
    path('trip/itinerary/', itinerary_view, name='itinerary'),
    path('trip/summary/', trip_summary_view, name='trip_summary'),
    path('dashboard/saved/', view_saved_trips, name='view_saved_trips'),
    path('trip/view/<int:trip_id>/', view_trip, name='view_trip'),
    path('trip/delete/<int:trip_id>/', delete_trip, name='delete_trip'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
