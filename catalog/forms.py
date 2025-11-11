from django import forms
from django.forms import inlineformset_factory
from .models import Artwork, ArtworkImage, Rating, Comment


# --- ASAR YARATISH FORMASI ---
class ArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = ['title', 'price', 'description', 'contact', 'telegram', 'category']
        labels = {
            'title': "Asar nomi",
            'price': "Narx (so'm)",
            'description': "Tavsif",
            'contact': "Aloqa raqami",
            'telegram': "Telegram manzili (ixtiyoriy)",
            'category': "Kategoriya",
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Masalan: Yog‘li bo‘yoqda gul rasmi',
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'placeholder': 'Masalan: 250000',
                'class': 'form-control',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Asar haqida qisqacha ma’lumot yozing...',
                'class': 'form-control'
            }),
            'contact': forms.TextInput(attrs={
                'placeholder': '+998901234567',
                'class': 'form-control'
            }),
            'telegram': forms.TextInput(attrs={
                'placeholder': '@username (ixtiyoriy)',
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    # --- NARXNI TEKSHIRISH ---
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Narx musbat bo‘lishi kerak.")
        return price

    # --- ALOQA RAQAMINI TEKSHIRISH ---
    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '').strip()
        if not contact:
            raise forms.ValidationError("Aloqa maydoni bo‘sh bo‘lmasin.")
        return contact

    # --- TELEGRAM MAYDONINI TOZALASH VA FORMATLASH ---
    def clean_telegram(self):
        telegram = self.cleaned_data.get('telegram', '').strip()
        if telegram:
            # agar foydalanuvchi faqat username kiritsa
            if not telegram.startswith('@') and 't.me/' not in telegram:
                telegram = '@' + telegram
        return telegram


# --- RASMLAR UCHUN FORMA ---
class ArtworkImageForm(forms.ModelForm):
    class Meta:
        model = ArtworkImage
        fields = ['image', 'order']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'order': forms.HiddenInput(),  # foydalanuvchiga ko‘rinmaydi
        }


# --- KO‘P RASMLI FORMA TO‘PLAMI ---
ArtworkImageFormSet = inlineformset_factory(
    Artwork,
    ArtworkImage,
    form=ArtworkImageForm,
    extra=3,
    max_num=3,
    can_delete=True,
    validate_max=True,
)


# --- REYTING BERISH FORMASI ---
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['value']
        widgets = {
            'value': forms.Select(
                choices=[(i, f"{i} ★") for i in range(1, 6)],
                attrs={'class': 'form-select'}
            )
        }


# --- IZOH QO‘SHISH FORMASI ---
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Fikringizni yozing...',
                'class': 'form-control'
            }),
        }
        labels = {
            'text': "Izoh matni"
        }
