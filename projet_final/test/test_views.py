import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_home_view():
    client = Client()
    response = client.get(reverse('home'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_login():
    username = 'testuser'
    password = 'Alpha12345'
    User.objects.create_user(username=username, password=password)
    client = Client()
    response = client.post(reverse('login'), {'username': username, 'password': password})
    assert response.status_code == 302 
    assert '_auth_user_id' in client.session

@pytest.mark.django_db
def test_logout():
    username = 'testuser'
    password = 'Alpha12345'
    user = User.objects.create_user(username=username, password=password)
    client = Client()
    client.login(username=username, password=password)
    assert '_auth_user_id' in client.session
    response = client.get(reverse('logout'))
    assert '_auth_user_id' not in client.session
    assert response.status_code == 302  
    assert response.url == reverse('home')  
    
@pytest.mark.django_db
def test_inscription_view():
    client = Client()
    response = client.get(reverse('inscription'))
    assert response.status_code == 200
    
@pytest.mark.django_db
def test_inscription_invalid_post_data():
    client = Client()
    user_data = {
        'username': 'newuser',
        'password1': 'password123',
        'password2': 'password1234',  
    }
    response = client.post(reverse('inscription'), user_data)
    assert 'form' in response.context
    assert response.context['form'].errors  

@pytest.mark.django_db
def test_successful_inscription():
    client = Client()
    user_data = {
        'username': 'validuser',
        'password1': 'Validpassword123',
        'password2': 'Validpassword123',
    }
    response = client.post(reverse('inscription'), user_data)
    assert response.status_code == 302  # Redirection après inscription réussie
    assert User.objects.filter(username='validuser').exists()

@pytest.mark.django_db
def test_failed_inscription():
    client = Client()
    user_data = {
        'username': 'user',
        'password1': 'password',
        'password2': 'password123',  # Mots de passe différents
    }
    response = client.post(reverse('inscription'), user_data)
    assert response.status_code == 200  # Pas de redirection
    assert 'form' in response.context
    assert response.context['form'].is_valid() == False
    
@pytest.mark.django_db
def test_failed_login():
    client = Client()
    response = client.post(reverse('login'), {'username': 'wronguser', 'password': 'wrongpassword'})
    assert response.status_code == 200  # Pas de redirection
    assert '_auth_user_id' not in client.session

