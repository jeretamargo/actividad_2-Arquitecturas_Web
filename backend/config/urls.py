from django.contrib import admin
from django.urls import include, path





urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("activities.api.v1.urls")),  
   # path("v2/", include("activities.api.v2.urls")),
    
]
