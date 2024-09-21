from django import forms
from .models import Center, Section, SectionCategory

class CenterForm(forms.ModelForm):
    class Meta:
        model = Center
        fields = ['name', 'description', 'location', 'image'] 

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'category', 'image']  

class SectionCategoryForm(forms.ModelForm):
    class Meta:
        model = SectionCategory
        fields = ['name', 'image']
