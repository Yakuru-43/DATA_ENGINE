from django.forms import ModelForm, TextInput, NumberInput
from django.forms.widgets import Select, SelectMultiple
from cet.models import segmentsCna
from django import forms

class segmentsCnaForm(ModelForm):
    class Meta:
        model = segmentsCna
        fields = ["cna_order", "name","is_total"]
        widgets = {
            'cna_order': NumberInput(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'is_total': forms.Select(choices=[("Y", "Y"), ("N", "N")]),
        }
