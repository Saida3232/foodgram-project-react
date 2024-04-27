from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.v1.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL)