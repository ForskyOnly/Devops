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

