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
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import warnings
from dotenv import load_dotenv
import logging
from queue import Queue
import time
from django.views.decorators.http import require_http_methods
import json
from django.conf import settings
from django.db.models import Q

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv('MISTRAL_API_KEY')
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
file_transcription = Queue()
transcription_en_cours = ""

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def start_recording(request):
    global enregistrement, trames, texte_transcrit, transcription, enregistrement_termine, file_transcription, transcription_en_cours
    enregistrement = True
    trames = []
    texte_transcrit = ""
    transcription = None
    enregistrement_termine.clear()
    file_transcription = Queue()
    transcription_en_cours = ""

    thread = threading.Thread(target=enregistrer_audio_et_transcrire, args=(request.user,))
    thread.start()

    return JsonResponse({'status': 'Enregistrement démarré'})

@login_required
def stop_recording(request):
    global enregistrement, transcription, enregistrement_termine
    enregistrement = False
    enregistrement_termine.wait()
    
    if transcription is not None:
        texte_transcrit = transcription.text
        logger.debug(f"Transcription générée : {texte_transcrit[:100]}...")  # Affiche les 100 premiers caractères
        return JsonResponse({
            'status': 'Enregistrement arrêté',
            'texte_transcrit': texte_transcrit
        })
    else:
        return JsonResponse({'status': 'Erreur lors de l\'enregistrement', 'texte_transcrit': ''}, status=500)

@login_required
def get_current_transcription(request):
    global transcription_en_cours
    nouvelle_transcription = ""
    
    while not file_transcription.empty():
        nouvelle_transcription += file_transcription.get() + " "
    
    transcription_en_cours += nouvelle_transcription
    
    return JsonResponse({
        'transcription': nouvelle_transcription,
        'transcription_complete': transcription_en_cours
    })

@login_required
@require_http_methods(["POST"])
def save_and_summarize(request):
    data = json.loads(request.body)
    texte = data['texte']
    
    # Récupérer le dernier enregistrement audio de l'utilisateur
    audio = Audio.objects.filter(user=request.user).latest('created_at')
    
    # Créer ou mettre à jour la transcription
    transcription, created = Transcription.objects.update_or_create(
        audio=audio,
        defaults={'text': texte}
    )
    
    # Générer le résumé et le titre
    resume_texte, titre = generate_summary_and_title(texte, transcription.id)
    
    return JsonResponse({
        'texte_sauvegarde': transcription.text,
        'resume_texte': resume_texte,
        'titre': titre
    })

def enregistrer_audio_et_transcrire(user):
    global enregistrement, trames, texte_transcrit, transcription, enregistrement_termine, file_transcription

    bloc_taille = 1024
    format_echantillon = pyaudio.paInt16
    canaux = 2
    taux_echantillonnage = 44100
    segment_duree = 5  # Durée du segment en secondes

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

        # Transcrivez le segment
        fichier_segment = "segment_temp.wav"
        with wave.open(fichier_segment, 'wb') as wf:
            wf.setnchannels(canaux)
            wf.setsampwidth(p.get_sample_size(format_echantillon))
            wf.setframerate(taux_echantillonnage)
            wf.writeframes(b''.join(trames))

        try:
            resultat = modele.transcribe(fichier_segment, language='fr')
            texte_segment = resultat["text"].strip()
            texte_transcrit += texte_segment + " "
            file_transcription.put(texte_segment)
        except Exception as e:
            logger.error(f"Erreur lors de la transcription : {str(e)}")

        trames.clear()

    flux.stop_stream()
    flux.close()
    p.terminate()

    try:
        fichier_audio = Audio(user=user, file=fichier_segment)
        fichier_audio.save()

        transcription = Transcription(audio=fichier_audio, text=texte_transcrit)
        transcription.save()

        # Supprimer le fichier audio après la transcription
        if os.path.exists(fichier_segment):
            os.remove(fichier_segment)

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'audio ou de la transcription: {e}")
        transcription = None
    finally:
        # Indiquer que l'enregistrement est terminé
        enregistrement_termine.set()

def generate_summary_and_title(texte, transcription_id=None):
    api_key = settings.MISTRAL_API_KEY
    logger.debug(f"API Key: {api_key[:5] if api_key else 'Not found'}...")  # Pour le débogage
    client = MistralClient(api_key=api_key)
    modele = "mistral-large-2402"

    # Générer le résumé
    message_resume = (
        f"Résumez cette transcription de réunion : {texte}\n\n"
        "Instructions :\n"
        "1. Produisez un résumé concis et professionnel en français.\n"
        "2. Concentrez-vous sur les points clés, les décisions prises et les actions à entreprendre.\n"
        "3. Utilisez un langage formel et adapté au contexte d'entreprise.\n"
        "4. Structurez le résumé avec des paragraphes clairs et des puces si nécessaire.\n"
        "5. Assurez-vous que le résumé soit objectif et précis, sans interprétation personnelle.\n"
        "6. Si la transcription n'est pas en français, traduisez le résumé en français.\n"
        "7. Évitez toute mention de 'Le texte prescrit' ou de la nature de la tâche.\n"
        "8. Limitez-vous aux informations fournies dans la transcription.\n"
    )

    reponse_resume = client.chat(
        model=modele,
        messages=[ChatMessage(role="user", content=message_resume)],
        safe_mode=True
    )

    resume_texte = reponse_resume.choices[0].message.content

    # Générer le titre
    message_titre = (
        f"Basé sur ce résumé de réunion, générez un titre court et percutant en français : {resume_texte}\n\n"
        "Instructions :\n"
        "1. Le titre doit être court (maximum 10 mots).\n"
        "2. Il doit capturer l'essence ou le sujet principal de la réunion.\n"
        "3. Utilisez un langage formel et professionnel.\n"
        "4. Évitez les articles au début du titre si possible.\n"
        "5. N'incluez pas de ponctuation à la fin du titre.\n"
    )

    reponse_titre = client.chat(
        model=modele,
        messages=[ChatMessage(role="user", content=message_titre)],
        safe_mode=True
    )

    titre = reponse_titre.choices[0].message.content

    # Si un ID de transcription est fourni, sauvegardez le résumé et le titre
    if transcription_id:
        try:
            transcription = Transcription.objects.get(id=transcription_id)
            summary = Summary(transcription=transcription, text=resume_texte)
            summary.save()
            
            # Mettre à jour le titre de l'audio associé
            transcription.audio.title = titre
            transcription.audio.save()
            
            logger.debug(f"Résumé sauvegardé: {summary.id}, Titre généré: {titre}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du résumé ou du titre: {e}")

    return resume_texte, titre

@method_decorator(csrf_protect, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'

@login_required
def profil(request):
    sort_by = request.GET.get('sort', '-created_at')  # Par défaut, tri par date décroissante
    search_query = request.GET.get('search', '')

    transcriptions = Transcription.objects.filter(audio__user=request.user)
    summaries = Summary.objects.filter(transcription__audio__user=request.user)

    if search_query:
        transcriptions = transcriptions.filter(
            Q(audio__title__icontains=search_query) | 
            Q(text__icontains=search_query)
        )
        summaries = summaries.filter(
            Q(transcription__audio__title__icontains=search_query) | 
            Q(text__icontains=search_query)
        )

    transcriptions = transcriptions.order_by(sort_by)
    summaries = summaries.order_by(sort_by)

    return render(request, 'profil.html', {
        'transcriptions': transcriptions,
        'summaries': summaries,
        'current_sort': sort_by,
        'search_query': search_query,
    })

@login_required
def get_transcription(request, id):
    transcription = Transcription.objects.get(id=id, audio__user=request.user)
    return JsonResponse({
        'title': transcription.audio.title if transcription.audio else 'Sans titre',
        'text': transcription.text,
    })

@login_required
def get_summary(request, id):
    summary = Summary.objects.get(id=id, transcription__audio__user=request.user)
    return JsonResponse({
        'title': summary.transcription.audio.title if summary.transcription.audio else 'Sans titre',
        'text': summary.text,
    })

def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.body)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'inscription.html', {'form': form})
