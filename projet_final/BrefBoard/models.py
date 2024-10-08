# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



# model pour la gestion des audios

class Audio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='audios/')
    created_at = models.DateTimeField(default=timezone.now)

# model pour la gestion des transcriptions

class Transcription(models.Model):
    audio = models.OneToOneField(Audio, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# model pour la gestion des résumés

class Summary(models.Model):
    transcription = models.OneToOneField(Transcription, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

