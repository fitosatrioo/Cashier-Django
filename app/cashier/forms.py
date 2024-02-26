from .models import Gun, Order
from django import forms

# - Create a record
class CreateGunForm(forms.ModelForm):

    class Meta:
        model = Gun
        fields = ['name', 'price', 'stock', 'description', 'image']


# - Update a record
class UpdateGunForm(forms.ModelForm):

    class Meta:
        model = Gun
        fields = ['name', 'price', 'stock', 'description', 'image']

#buy gun
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['gun', 'quantity']
