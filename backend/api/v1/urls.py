from django.urls import path, include

urlpatterns = [
  #path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]