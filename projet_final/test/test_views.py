from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from BrefBoard.models import Audio, Transcription, Summary
from unittest.mock import patch

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertTrue(True)  

    @patch('BrefBoard.views.enregistrer_audio_et_transcrire')
    def test_start_recording(self, mock_enregistrer):
        response = self.client.post(reverse('start_recording'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'Enregistrement démarré'})
        mock_enregistrer.assert_called_once()
        self.assertTrue(True)  

    def test_stop_recording(self):
        # Simuler une transcription
        audio = Audio.objects.create(user=self.user)
        transcription = Transcription.objects.create(audio=audio, text="Test transcription")
        
        with patch('BrefBoard.views.transcription', transcription):
            response = self.client.post(reverse('stop_recording'))
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(str(response.content, encoding='utf8'), {
                'status': 'Enregistrement arrêté',
                'texte_transcrit': 'Test transcription'
            })
        self.assertTrue(True)  

    @patch('BrefBoard.views.generate_summary_and_title')
    def test_save_and_summarize(self, mock_generate):
        mock_generate.return_value = ("Résumé test", "Titre test")
        
        audio = Audio.objects.create(user=self.user)
        Transcription.objects.create(audio=audio, text="Texte original")

        response = self.client.post(reverse('save_and_summarize'), 
                                    {'texte': 'Nouveau texte'}, 
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['texte_sauvegarde'], 'Nouveau texte')
        self.assertEqual(data['resume_texte'], 'Résumé test')
        self.assertEqual(data['titre'], 'Titre test')
        self.assertTrue(True)  

    def test_profil_view(self):
        response = self.client.get(reverse('profil'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profil.html')
        self.assertTrue(True)  

    def test_get_transcription(self):
        audio = Audio.objects.create(user=self.user, title="Test Audio")
        transcription = Transcription.objects.create(audio=audio, text="Test transcription")
        
        response = self.client.get(reverse('get_transcription', args=[transcription.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {
            'title': 'Test Audio',
            'text': 'Test transcription'
        })
        self.assertTrue(True) 

