from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/usuarios/login/'), name='logout'),
    path('permissoes/', views.permissoes, name='permissoes'),
    path('tornar_gerente/<int:id>', views.tornar_gerente, name='tornar_gerente'),
]