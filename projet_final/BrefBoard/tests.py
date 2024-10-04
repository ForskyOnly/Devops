from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from BrefBoard.models import Audio, Transcription, Summary
from BrefBoard.forms import CustomUserCreationForm
from django.conf import settings

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.audio = Audio.objects.create(user=self.user, title="Test Audio")
        self.transcription = Transcription.objects.create(audio=self.audio, text="Test transcription")
        self.summary = Summary.objects.create(transcription=self.transcription, text="Test summary")

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_profil_view(self):
        response = self.client.get(reverse('profil'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profil.html')
        self.assertIn('transcriptions', response.context)
        self.assertIn('summaries', response.context)

    def test_login_required(self):
        self.client.logout()
        protected_urls = ['home', 'profil', 'start_recording', 'stop_recording', 'save_and_summarize']
        for url_name in protected_urls:
            response = self.client.get(reverse(url_name))
            self.assertRedirects(response, f"{reverse('login')}?next={reverse(url_name)}")

    def test_inscription(self):
        self.client.logout()
        response = self.client.post(reverse('inscription'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })
        self.assertEqual(response.status_code, 302)  # On s'attend maintenant à une redirection
        
        # Vérifier si l'utilisateur existe
        user_exists = User.objects.filter(username='newuser').exists()
        self.assertTrue(user_exists)
        
        # Optionnel : vérifier l'URL de redirection
        self.assertRedirects(response, reverse('home'))  # Remplacez 'home' par l'URL réelle de redirection
            
            
    def test_login(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': '12345'
        })
        self.assertEqual(response.status_code, 302)  # Redirection après connexion réussie


    def test_get_transcription(self):
        response = self.client.get(reverse('get_transcription', args=[self.transcription.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {
            'title': 'Test Audio',
            'text': 'Test transcription'
        })

    def test_get_summary(self):
        response = self.client.get(reverse('get_summary', args=[self.summary.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {
            'title': 'Test Audio',
            'text': 'Test summary'
        })

    def test_delete_transcription(self):
        response = self.client.post(reverse('delete_transcription', args=[self.transcription.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'success'})
        self.assertFalse(Transcription.objects.filter(id=self.transcription.id).exists())

    def test_delete_summary(self):
        response = self.client.post(reverse('delete_summary', args=[self.summary.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'status': 'success'})
        self.assertFalse(Summary.objects.filter(id=self.summary.id).exists())

    def test_download_pdf(self):
        response = self.client.get(reverse('download_pdf'), {'title': 'Test', 'content': 'Test content'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="Test.pdf"')

class FormTestCase(TestCase):
    def test_custom_user_creation_form(self):
        form_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',  # Ajout de l'email
            'password1': 'Complexpassword123',
            'password2': 'Complexpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        if not form.is_valid():
            print(form.errors)  # Affiche les erreurs si le formulaire n'est pas valide
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_password_mismatch(self):
        form_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',  # Ajout de l'email
            'password1': 'complexpassword123',
            'password2': 'differentpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    # Vous pouvez ajouter un test supplémentaire pour vérifier la validation de l'email
    def test_custom_user_creation_form_invalid_email(self):
        form_data = {
            'username': 'testuser',
            'email': 'invalid-email',  # Email invalide
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
class ModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.audio = Audio.objects.create(user=self.user, title="Test Audio")
        self.transcription = Transcription.objects.create(audio=self.audio, text="Test transcription")
        self.summary = Summary.objects.create(transcription=self.transcription, text="Test summary")

    def test_audio_model(self):
        self.assertEqual(str(self.audio), f"Audio object ({self.audio.id})")
        self.assertEqual(self.audio.user, self.user)
        self.assertEqual(self.audio.title, "Test Audio")

    def test_transcription_model(self):
        self.assertEqual(str(self.transcription), f"Transcription object ({self.transcription.id})")
        self.assertEqual(self.transcription.audio, self.audio)
        self.assertEqual(self.transcription.text, "Test transcription")

    def test_summary_model(self):
        self.assertEqual(str(self.summary), f"Summary object ({self.summary.id})")
        self.assertEqual(self.summary.transcription, self.transcription)
        self.assertEqual(self.summary.text, "Test summary")