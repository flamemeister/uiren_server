from django import forms
from .models import Center, Section

class CenterForm(forms.ModelForm):
    class Meta:
        model = Center
        fields = ['name', 'description', 'location', 'image']  # Добавляем поле image

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'category', 'image']  # Добавляем поле image
