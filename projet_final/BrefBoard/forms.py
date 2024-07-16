from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire personnalisé pour la création d'utilisateurs.
    
    Ce formulaire étend le formulaire de création d'utilisateur standard de Django
    pour ajuster les étiquettes, les textes d'aide et les messages d'erreur des champs,
    ainsi que pour personnaliser l'aspect des widgets.
    """
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        self.fields['username'].help_text = ""
        self.fields['username'].label = "Nom d'utilisateur"
        
        self.fields['password1'].help_text = " "
        self.fields['password1'].label = "Mot de passe"
        
        self.fields['password2'].help_text = ""
        self.fields['password2'].label = "Confirmez votre mot de passe"

        self.fields['username'].error_messages = {
            "required": "Entrez un nom d'utilisateur.",
            'unique': "Nom d'utilisateur déjà pris",
        }
        self.fields['password1'].error_messages = {
            'required': 'Entrez un mot de passe.',
            'password_mismatch': 'Les mots de passe ne correspondent pas.',
        }
        self.fields['password2'].error_messages = {
            'required': 'Confirmez votre mot de passe.',
            'password_mismatch': 'Les mots de passe ne correspondent pas.',
        }

        self.fields['username'].widget.attrs.update({"placeholder": "Nom d'utilisateur"})
        self.fields['password1'].widget.attrs.update({'placeholder': '8 carac min. chiffre lettres'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirmez votre mot de passe'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email'})
