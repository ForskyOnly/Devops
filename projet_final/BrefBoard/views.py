# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from .models import Audio, Transcription, Summary
import os
import threading
import pyaudio
import wave
import torch
import whisper
from pydub import AudioSegment
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import warnings
from dotenv import load_dotenv
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Charger le modèle Whisper au démarrage
try:
    appareil = "cuda" if torch.cuda.is_available() else "cpu"
    modele = whisper.load_model("small", device=appareil)
except RuntimeError as e:
    logger.error("Erreur CUDA, passage au CPU...")
    appareil = "cpu"
    modele = whisper.load_model("small", device=appareil)

# Variables globales pour gérer l'enregistrement
enregistrement = False
trames = []
texte_transcrit = ""
transcription = None
enregistrement_termine = threading.Event()

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def start_recording(request):
    global enregistrement, trames, texte_transcrit, transcription, enregistrement_termine
    enregistrement = True
    trames = []
    texte_transcrit = ""
    transcription = None
    enregistrement_termine.clear()

    thread = threading.Thread(target=enregistrer_audio_et_transcrire, args=(request.user,))
    thread.start()

    logger.debug("Enregistrement démarré")
    return JsonResponse({'status': 'Enregistrement démarré'})

@login_required
def stop_recording(request):
    global enregistrement, transcription, enregistrement_termine
    enregistrement = False
    logger.debug("Enregistrement arrêté")

    # Attendre que l'enregistrement soit complètement terminé
    enregistrement_termine.wait()
    
    if transcription is not None:
        logger.debug(f"Transcription ID: {transcription.id}")
        resume_texte = traduire_et_resumer(texte_transcrit, transcription.id)
        return JsonResponse({'status': 'Enregistrement arrêté', 'texte_transcrit': texte_transcrit, 'resume_texte': resume_texte})
    else:
        logger.error("Transcription est None")
        return JsonResponse({'status': 'Erreur lors de l\'enregistrement', 'texte_transcrit': '', 'resume_texte': ''}, status=500)

def enregistrer_audio_et_transcrire(user):
    global enregistrement, trames, texte_transcrit, transcription, enregistrement_termine

    bloc_taille = 1024  # Taille des blocs de données
    format_echantillon = pyaudio.paInt16  # Format des échantillons
    canaux = 2  # Nombre de canaux
    taux_echantillonnage = 44100  # Taux d'échantillonnage
    segment_duree = 5  # Durée de chaque segment en secondes

    # Initialiser l'interface PyAudio
    p = pyaudio.PyAudio()

    # Ouvrir le flux de données
    flux = p.open(format=format_echantillon,
                  channels=canaux,
                  rate=taux_echantillonnage,
                  frames_per_buffer=bloc_taille,
                  input=True)

    while enregistrement:
        for _ in range(0, int(taux_echantillonnage / bloc_taille * segment_duree)):
            if not enregistrement:
                break
            donnees = flux.read(bloc_taille)
            trames.append(donnees)

        # Sauvegarder le segment en format WAV
        fichier_segment = "segment_temp.wav"
        with wave.open(fichier_segment, 'wb') as wf:
            wf.setnchannels(canaux)
            wf.setsampwidth(p.get_sample_size(format_echantillon))
            wf.setframerate(taux_echantillonnage)
            wf.writeframes(b''.join(trames))

        # Transcrire le segment
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            resultat = modele.transcribe(fichier_segment, language='fr')
        texte_transcrit += resultat["text"] + " "
        trames.clear()

    flux.stop_stream()
    flux.close()
    p.terminate()

    try:
        fichier_audio = Audio(user=user, file=fichier_segment)
        fichier_audio.save()
        logger.debug(f"Audio sauvegardé: {fichier_audio.id}")

        transcription = Transcription(audio=fichier_audio, text=texte_transcrit)
        transcription.save()
        logger.debug(f"Transcription sauvegardée: {transcription.id}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'audio ou de la transcription: {e}")
        transcription = None
    finally:
        # Indiquer que l'enregistrement est terminé
        enregistrement_termine.set()

def traduire_et_resumer(texte, transcription_id):
    cle_api = os.environ["API_KEY"]
    modele = "mistral-large-2402"
    
    client = MistralClient(api_key=cle_api)

    message = (
        f"résumez cette transciption : {texte}. "
        "Toujours assister avec soin, respect et vérité. Répondre avec une utilité maximale tout en assurant la sécurité. Éviter les contenus nuisibles, non éthiques, préjudiciables ou négatifs. Veiller à ce que les réponses promeuvent l'équité et la positivité."
        "Le résumé doit souligner les points importants en utilisant un style formel et professionnel."
        "Il doit être structuré avec des paragraphes clairs et concis, en mettant l'accent sur les principaux thèmes et conclusions. "
        "Assurez-vous que le résumé soit bien structuré, facile à lire, et qu'il fournisse une vue d'ensemble complète et précise de la transcription. "
    )

    reponse_chat = client.chat(
        model=modele,
        messages=[ChatMessage(role="user", content=message)],
        safe_mode=True
    )

    resume_texte = reponse_chat.choices[0].message.content

    try:
        transcription = Transcription.objects.get(id=transcription_id)
        summary = Summary(transcription=transcription, text=resume_texte)
        summary.save()
        logger.debug(f"Résumé sauvegardé: {summary.id}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du résumé: {e}")

    return resume_texte

class CustomLoginView(LoginView):
    template_name = 'login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'

@login_required
def profil(request):
    audios = Audio.objects.filter(user=request.user)
    transcriptions = Transcription.objects.filter(audio__user=request.user)
    summaries = Summary.objects.filter(transcription__audio__user=request.user)
    return render(request, 'profil.html', {
        'audios': audios,
        'transcriptions': transcriptions,
        'summaries': summaries
    })

def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'inscription.html', {'form': form})
