from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
from django.conf import settings
from .forms import CustomUserCreationForm
from .models import Audio, Transcription, Summary
from .metrics import (
    ERROR_COUNTER, EXCEPTION_COUNTER, VIEW_LATENCY, REQUEST_COUNT,
    AUDIO_RECORDINGS, TRANSCRIPTION_DURATION, WHISPER_PROCESSING_TIME,
    WHISPER_ERRORS, AUDIO_DURATION, RECORDING_ERRORS,
    monitor_view, count_requests, monitor_whisper_processing, record_audio_duration,
    measure_duration
)
import os
import threading
import pyaudio
import wave
import torch
import whisper
from pydub import AudioSegment
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv
import logging
from queue import Queue
import time
import json
from reportlab.pdfgen import canvas
from io import BytesIO
from prometheus_client import Counter, Histogram
import requests

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv('MISTRAL_API_KEY')

@monitor_view
@count_requests
@login_required
@csrf_protect
def prediction_view(request):
    """
    View pour la prédiction de la catégorie de l'audio en fonction du texte transcrit, ARGS: input_text, RETURN: render
    """
    prediction_result = None
    if request.method == 'POST':
        input_text = request.POST.get('input_text')
        
        api_url = "http://dcpclassification-unique-dns.francecentral.azurecontainer.io:8000/predict"
        
        headers = {
            settings.API_KEY_NAME: settings.API_KEY
        }
        
        data = {"text": input_text}
        
        try:
            response = requests.post(api_url, json=data, headers=headers)
            response.raise_for_status()
            prediction_result = response.json().get('prediction')
            logger.info(f"Prédiction réussie pour l'utilisateur {request.user.username}")
        except requests.RequestException as e:
            ERROR_COUNTER.labels(type='prediction_api_error').inc()
            prediction_result = f"Erreur : {str(e)}"
            logger.error(f"Erreur lors de la prédiction pour l'utilisateur {request.user.username}: {str(e)}")

    return render(request, 'prediction.html', {'prediction_result': prediction_result})


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

#  métriques pour le résumé
SUMMARIES_GENERATED = Counter('django_summaries_generated_total', 'Number of summaries generated')
SUMMARY_GENERATION_TIME = Histogram('django_summary_generation_seconds', 'Time taken to generate summary')

@monitor_view
@count_requests
@login_required
def home(request):
    logger.info("Accès à la page d'accueil par l'utilisateur %s", request.user.username)
    return render(request, 'home.html')

@monitor_view
@count_requests
@login_required
@require_POST
@ensure_csrf_cookie
def start_recording(request):
    global enregistrement, trames, texte_transcrit, transcription, enregistrement_termine, file_transcription, transcription_en_cours
    """
    View pour démarrer l'enregistrement de l'audio, ARGS: request, RETUNR: JsonResponse
    """
    logger.info("Démarrage de l'enregistrement pour l'utilisateur %s", request.user.username)
    AUDIO_RECORDINGS.inc()
    enregistrement = True
    trames = []
    texte_transcrit = ""
    transcription = None
    enregistrement_termine.clear()
    file_transcription = Queue()
    transcription_en_cours = ""

    logger.debug("Avant le démarrage du thread")
    thread = threading.Thread(target=enregistrer_audio_et_transcrire, args=(request.user,))
    thread.start()
    logger.debug("Après le démarrage du thread")

    logger.debug("Thread d'enregistrement démarré")
    return JsonResponse({'status': 'Enregistrement démarré'})

@monitor_view
@count_requests
@login_required
@require_POST
@ensure_csrf_cookie
def stop_recording(request):
    """
    View pour arrêter l'enregistrement de l'audio, ARGS: request, RETOURNE: JsonResponse
    """
    global enregistrement, transcription, enregistrement_termine
    logger.info("Arrêt de l'enregistrement pour l'utilisateur %s", request.user.username)
    enregistrement = False
    enregistrement_termine.wait()
    
    if transcription is not None:
        texte_transcrit = transcription.text
        logger.debug(f"Transcription générée : {texte_transcrit[:100]}...")
        return JsonResponse({
            'status': 'Enregistrement arrêté',
            'texte_transcrit': texte_transcrit
        })
    else:
        ERROR_COUNTER.labels(type='transcription_failed').inc()
        return JsonResponse({'status': 'Erreur lors de l\'enregistrement', 'texte_transcrit': ''}, status=500)

@monitor_view
@count_requests
@login_required
@ensure_csrf_cookie
def get_current_transcription(request):
    """
    View pour récupérer la transcription en cours, ARGS: request, RETOURNE: JsonResponse
    """
    logger.debug("Récupération de la transcription en cours pour l'utilisateur %s", request.user.username)
    global transcription_en_cours
    nouvelle_transcription = ""
    
    while not file_transcription.empty():
        nouvelle_transcription += file_transcription.get() + " "
    
    transcription_en_cours += nouvelle_transcription
    
    return JsonResponse({
        'transcription': nouvelle_transcription,
        'transcription_complete': transcription_en_cours
    })

@monitor_view
@count_requests
@login_required
@require_POST
@ensure_csrf_cookie
def save_and_summarize(request):
    """
    View pour sauvegarder et résumer la transcription, ARGS: request, RETURN: JsonResponse
    """
    logger.info("Sauvegarde et résumé de la transcription pour l'utilisateur %s", request.user.username)
    data = json.loads(request.body)
    texte = data['texte']
    
    audio = Audio.objects.filter(user=request.user).latest('created_at')
    
    transcription, created = Transcription.objects.update_or_create(
        audio=audio,
        defaults={'text': texte}
    )
    
    resume_texte, titre = generate_summary_and_title(texte, transcription.id)
    
    return JsonResponse({
        'texte_sauvegarde': transcription.text,
        'resume_texte': resume_texte,
        'titre': titre
    })

@measure_duration(TRANSCRIPTION_DURATION)
@monitor_whisper_processing
def enregistrer_audio_et_transcrire(user):
    """
    Fonction pour enregistrer l'audio et transcrire le texte, ARGS: user, RETURN: None
    """
    logger.debug("Début de la fonction enregistrer_audio_et_transcrire")
    global enregistrement, trames, texte_transcrit, transcription, enregistrement_termine, file_transcription

    bloc_taille = 1024
    format_echantillon = pyaudio.paInt16
    canaux = 2
    taux_echantillonnage = 44100
    segment_duree = 5

    p = pyaudio.PyAudio()

    flux = p.open(format=format_echantillon,
                  channels=canaux,
                  rate=taux_echantillonnage,
                  frames_per_buffer=bloc_taille,
                  input=True)

    start_time = time.time()
    while enregistrement:
        for _ in range(0, int(taux_echantillonnage / bloc_taille * segment_duree)):
            if not enregistrement:
                break
            donnees = flux.read(bloc_taille)
            trames.append(donnees)

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
            WHISPER_ERRORS.labels(error_type=type(e).__name__).inc()
            logger.error(f"Erreur lors de la transcription : {str(e)}")

        trames.clear()

    flux.stop_stream()
    flux.close()
    p.terminate()

    record_audio_duration(time.time() - start_time)

    try:
        fichier_audio = Audio(user=user, file=fichier_segment)
        fichier_audio.save()

        transcription = Transcription(audio=fichier_audio, text=texte_transcrit)
        transcription.save()

        if os.path.exists(fichier_segment):
            os.remove(fichier_segment)

    except Exception as e:
        ERROR_COUNTER.labels(type='audio_save_error').inc()
        logger.exception("Erreur lors de la sauvegarde de l'audio ou de la transcription: %s", str(e))
        transcription = None
    finally:
        enregistrement_termine.set()
        logger.info("Fin de l'enregistrement et de la transcription pour l'utilisateur %s", user.username)

@measure_duration(SUMMARY_GENERATION_TIME)
def generate_summary_and_title(texte, transcription_id=None):
    """
    Fonction pour générer le résumé et le titre de la transcription, ARGS: texte, transcription_id, RETURN: resume_texte, titre
    """
    logger.info("Génération du résumé et du titre pour la transcription %s", transcription_id)
    api_key = settings.MISTRAL_API_KEY
    client = MistralClient(api_key=api_key)
    modele = "mistral-large-2402"

    message_resume = (
        f"Faites un résumé professionnel de cette transcription: {texte}\n\n"
        "Instructions :\n"
        "1. Produisez un résumé très concis et professionnel en français.\n"
        "2. Concentrez-vous uniquement sur les informations présentes dans la transcription.\n"
        "3. N'ajoutez aucune information ou interprétation qui n'est pas explicitement mentionnée.\n"
        "4. Utilisez un langage formel et adapté au contexte d'entreprise.\n"
        "5. Si la transcription est trop courte ou manque de contenu, reflétez simplement ce fait dans le résumé.\n"
        "6. Évitez toute spéculation ou élaboration au-delà du contenu fourni.\n"
    )

    messages = [ChatMessage(role="user", content=message_resume)]
    
    reponse_resume = client.chat(model=modele, messages=messages)
    resume_texte = reponse_resume.choices[0].message.content

    message_titre = (
        f"Basé sur ce résumé de réunion, générez un titre court et percutant en français : {resume_texte}\n\n"
        "Instructions :\n"
        "1. Le titre doit être court (maximum 10 mots).\n"
        "2. Il doit capturer l'essence ou le sujet principal de la réunion.\n"
        "3. Utilisez un langage formel et professionnel.\n"
        "4. Évitez les articles au début du titre si possible.\n"
        "5. N'incluez pas de ponctuation à la fin du titre.\n"
    )

    messages = [ChatMessage(role="user", content=message_titre)]
    
    reponse_titre = client.chat(model=modele, messages=messages)
    titre = reponse_titre.choices[0].message.content

    SUMMARIES_GENERATED.inc()

    if transcription_id:
        try:
            transcription = Transcription.objects.get(id=transcription_id)
            summary = Summary(transcription=transcription, text=resume_texte)
            summary.save()
            
            transcription.audio.title = titre
            transcription.audio.save()
            
            logger.debug(f"Résumé sauvegardé: {summary.id}, Titre généré: {titre}")
        except Exception as e:
            ERROR_COUNTER.labels(type='summary_generation_error').inc()
            logger.exception("Erreur lors de la sauvegarde du résumé ou du titre: %s", str(e))

    return resume_texte, titre

@method_decorator(csrf_protect, name='dispatch')
@method_decorator(monitor_view, name='dispatch')
@method_decorator(count_requests, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        """
        Fonction pour gérer la connexion réussie, ARGS: form, RETURN: super().form_valid(form)
        """
        logger.info("Connexion réussie pour l'utilisateur %s", form.get_user())
        return super().form_valid(form)
    
class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        logger.info("Connexion réussie pour l'utilisateur %s", form.get_user())
        return super().form_valid(form)

@method_decorator(monitor_view, name='dispatch')
@method_decorator(count_requests, name='dispatch')
class CustomLogoutView(LogoutView):
    next_page = 'login'

    def dispatch(self, request, *args, **kwargs):
        logger.info("Déconnexion de l'utilisateur %s", request.user.username)
        return super().dispatch(request, *args, **kwargs)

@monitor_view
@count_requests
@login_required
def profil(request):
    """
    View pour afficher le profil de l'utilisateur, ARGS: request, RETURN: render
    """
    logger.info("Accès au profil pour l'utilisateur %s", request.user.username)
    sort_by = request.GET.get('sort', '-created_at')
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

@monitor_view
@count_requests
@login_required
def get_transcription(request, id):
    """
    View pour récupérer la transcription, ARGS: request, id, RETURN: JsonResponse
    """
    logger.debug("Récupération de la transcription %s pour l'utilisateur %s", id, request.user.username)
    transcription = Transcription.objects.get(id=id, audio__user=request.user)
    return JsonResponse({
        'title': transcription.audio.title if transcription.audio else 'Sans titre',
        'text': transcription.text,
    })

@monitor_view
@count_requests
@login_required
def get_summary(request, id):
    """
    View pour récupérer le résumé, ARGS: request, id, RETURN: JsonResponse
    """
    logger.debug("Récupération du résumé %s pour l'utilisateur %s", id, request.user.username)
    summary = Summary.objects.get(id=id, transcription__audio__user=request.user)
    return JsonResponse({
        'title': summary.transcription.audio.title if summary.transcription.audio else 'Sans titre',
        'text': summary.text,
    })


@monitor_view
@count_requests
@csrf_protect
def inscription(request):
    """
    View pour l'inscription d'un nouvel utilisateur, ARGS: request, RETURN: render
    """
    if request.method == 'POST':
        logger.info("Tentative d'inscription d'un nouvel utilisateur")
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        logger.debug("Affichage du formulaire d'inscription")
        form = CustomUserCreationForm()
    return render(request, 'inscription.html', {'form': form})


@monitor_view
@count_requests
@login_required
def download_pdf(request):
    """
    View pour télécharger un PDF, ARGS: request, RETURN: HttpResponse
    """
    logger.info("Téléchargement de PDF pour l'utilisateur %s", request.user.username)
    title = request.GET.get('title', 'Document')
    content = request.GET.get('content', '')

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    
    p.drawString(100, 750, title)
    
    y = 730
    for line in content.split('\n'):
        if y < 50:
            p.showPage()
            y = 750
        p.drawString(100, y, line)
        y -= 15

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title}.pdf"'
    response.write(pdf)

    return response

@monitor_view
@count_requests
@login_required
@require_POST
def delete_transcription(request, id):
    """
    View pour supprimer la transcription, ARGS: request, id, RETURN: JsonResponse
    """
    logger.info("Suppression de la transcription %s pour l'utilisateur %s", id, request.user.username)
    try:
        transcription = Transcription.objects.get(id=id, audio__user=request.user)
        transcription.delete()
        return JsonResponse({'status': 'success'})
    except Transcription.DoesNotExist:
        ERROR_COUNTER.labels(type='transcription_not_found').inc()
        logger.warning("Tentative de suppression d'une transcription inexistante (ID: %s) par l'utilisateur %s", id, request.user.username)
        return JsonResponse({'status': 'error'}, status=404)

@monitor_view
@count_requests
@login_required
@require_POST
def delete_summary(request, id):
    """
    View pour supprimer le résumé, ARGS: request, id, RETURN: JsonResponse
    """
    logger.info("Suppression du résumé %s pour l'utilisateur %s", id, request.user.username)
    try:
        summary = Summary.objects.get(id=id, transcription__audio__user=request.user)
        summary.delete()
        return JsonResponse({'status': 'success'})
    except Summary.DoesNotExist:
        ERROR_COUNTER.labels(type='summary_not_found').inc()
        logger.warning("Tentative de suppression d'un résumé inexistant (ID: %s) par l'utilisateur %s", id, request.user.username)
        return JsonResponse({'status': 'error'}, status=404)