"""projet_final URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from BrefBoard.views import (
    CustomLoginView, CustomLogoutView, home, profil, inscription, 
    start_recording, stop_recording, get_current_transcription, 
    get_transcription, save_and_summarize, get_summary, download_pdf, 
    delete_transcription, delete_summary, generate_summary_and_title, prediction_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('generate_summary/', generate_summary_and_title, name='generate_summary'),    
    path('', home, name='home'),
    path('profil/', profil, name='profil'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('inscription/', inscription, name='inscription'),
    path('start_recording/', start_recording, name='start_recording'),
    path('stop_recording/', stop_recording, name='stop_recording'),
    path('get_current_transcription/', get_current_transcription, name='get_current_transcription'),
    path('get_transcription/<int:id>/', get_transcription, name='get_transcription'),
    path('save_and_summarize/', save_and_summarize, name='save_and_summarize'),
    path('get_summary/<int:id>/', get_summary, name='get_summary'),
    path('download_pdf/', download_pdf, name='download_pdf'),
    path('delete_transcription/<int:id>/', delete_transcription, name='delete_transcription'),
    path('delete_summary/<int:id>/', delete_summary, name='delete_summary'),
    path('', include('django_prometheus.urls')),
    path('prediction/', prediction_view, name='prediction'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)