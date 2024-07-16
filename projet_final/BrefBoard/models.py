# models.py
from django.db import models
from django.contrib.auth.models import User

class Audio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='audios/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Transcription(models.Model):
    audio = models.ForeignKey(Audio, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Summary(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
