from django import forms
from django.forms import inlineformset_factory
from .models import Artwork, ArtworkImage, Rating, Comment


class ArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = ['title', 'price', 'description', 'contact', 'category']
        labels = {
            'price': "Narx (so'm)",
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Narx musbat bo‘lishi kerak.')
        return price

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '').strip()
        if not contact:
            raise forms.ValidationError('Aloqa maydoni bo‘sh bo‘lmasin.')
        return contact


class ArtworkImageForm(forms.ModelForm):
    class Meta:
        model = ArtworkImage
        fields = ['image', 'order']


ArtworkImageFormSet = inlineformset_factory(
    Artwork,
    ArtworkImage,
    form=ArtworkImageForm,
    extra=3,
    max_num=3,
    can_delete=True,
    validate_max=True,
)


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['value']
        widgets = {
            'value': forms.Select(choices=[(i, i) for i in range(1, 6)])
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3})
        }
