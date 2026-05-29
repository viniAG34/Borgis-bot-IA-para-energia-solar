from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('oraculo/', include('oraculo.urls')),
    path('', RedirectView.as_view(url='/oraculo/chat', permanent=False)),
]
