from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm
import os
import threading
import pyaudio
import wave
import torch
import whisper
from pydub import AudioSegment
from django.shortcuts import render, redirect
from django.http import JsonResponse
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import warnings
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required

load_dotenv()

# Charger le modèle Whisper au démarrage
try:
    appareil = "cuda" if torch.cuda.is_available() else "cpu"
    modele = whisper.load_model("small", device=appareil)
except RuntimeError as e:
    print("Erreur CUDA, passage au CPU...")
    appareil = "cpu"
    modele = whisper.load_model("small", device=appareil)

# Variables globales pour gérer l'enregistrement
enregistrement = False
trames = []
texte_transcrit = ""

@login_required
def home(request):
    return render(request, 'home.html')

def start_recording(request):
    global enregistrement, trames, texte_transcrit
    enregistrement = True
    trames = []
    texte_transcrit = ""

    thread = threading.Thread(target=enregistrer_audio_et_transcrire)
    thread.start()

    return JsonResponse({'status': 'Enregistrement démarré'})

def stop_recording(request):
    global enregistrement
    enregistrement = False
    return JsonResponse({'status': 'Enregistrement arrêté', 'texte_transcrit': texte_transcrit, 'resume_texte': traduire_et_resumer(texte_transcrit)})

def enregistrer_audio_et_transcrire():
    global enregistrement, trames, texte_transcrit

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
        wf = wave.open(fichier_segment, 'wb')
        wf.setnchannels(canaux)
        wf.setsampwidth(p.get_sample_size(format_echantillon))
        wf.setframerate(taux_echantillonnage)
        wf.writeframes(b''.join(trames))
        wf.close()

        # Transcrire le segment en français
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            resultat = modele.transcribe(fichier_segment, language="fr")
        texte_transcrit += resultat["text"] + " "

        # Réinitialiser les trames pour le prochain segment
        trames.clear()

    # Arrêter et fermer le flux de données
    flux.stop_stream()
    flux.close()
    p.terminate()

def traduire_et_resumer(texte):
    cle_api = os.environ["API_KEY"]
    modele = "mistral-large-2402"
    
    client = MistralClient(api_key=cle_api)

    message = (
        f"Traduisez le texte suivant en français s'il n'est pas déjà en français, puis résumez-le : {texte}. "
        "Le résumé doit souligner les points importants en utilisant un style formel et professionnel. "
        "Il doit être structuré avec des paragraphes clairs et concis, en mettant l'accent sur les principaux thèmes et conclusions. "
        "Évitez de mentionner que le résumé est destiné à être utilisé lors de réunions d'entreprise. "
        "Assurez-vous que le résumé soit bien structuré, facile à lire, et qu'il fournisse une vue d'ensemble complète et précise du texte. "
        "Peu importe la langue du texte source, le résumé doit toujours être en français."
    )

    reponse_chat = client.chat(
        model=modele,
        messages=[ChatMessage(role="user", content=message)],
        safe_mode=True
    )

    return reponse_chat.choices[0].message.content

class CustomLoginView(LoginView):
    template_name = 'login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'

@login_required
def profil(request):
    return render(request, 'profil.html')    

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
