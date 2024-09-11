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
from BrefBoard import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('generate_summary/',views.generate_summary_and_title, name='generate_summary'),    
    path('', views.home, name='home'),
    path('profil/', views.profil, name='profil'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('inscription/', views.inscription, name='inscription'),
    path('start_recording/', views.start_recording, name='start_recording'),
    path('stop_recording/', views.stop_recording, name='stop_recording'),
    path('get_current_transcription/', views.get_current_transcription, name='get_current_transcription'),
    path('get_transcription/<int:id>/', views.get_transcription, name='get_transcription'),
    path('save_and_summarize/', views.save_and_summarize, name='save_and_summarize'),
    path('get_summary/<int:id>/', views.get_summary, name='get_summary'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)