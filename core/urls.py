from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # This triggers the static minting logic we just wrote
    path('test-mint/', views.test_mint_view, name='test_mint'),
]