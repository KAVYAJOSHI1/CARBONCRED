from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing Page (new elite homepage)
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),

    # Main Application Dashboard
    path('app/', TemplateView.as_view(template_name='index.html'), name='app'),
    path('app', TemplateView.as_view(template_name='index.html'), name='app_noslash'),

    # API: AI verification & blockchain minting
    path('test-mint/', views.test_mint_view, name='test_mint'),
]