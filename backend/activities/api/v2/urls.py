from django.urls import path

from . import views


app_name = "activities"

urlpatterns = [
    
    path("activities/", views.ActivityListView.as_view(), name="api-activities-list"),
]