from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView





urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("activities.api.v1.urls")),  
    path("api/v2/", include("activities.api.v2.urls")),
   
]
