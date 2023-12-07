import pytest
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
def test_home_view():
    client = Client()
    response = client.get(reverse('home'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_inscription_view():
    client = Client()
    response = client.get(reverse('inscription'))
    assert response.status_code == 200

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
