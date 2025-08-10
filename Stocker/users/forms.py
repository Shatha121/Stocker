from django import forms

class ProductImportForm(forms.Form):
    csv_file = forms.FileField()