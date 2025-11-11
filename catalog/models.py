from __future__ import annotations
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import itertools


# --- SLUG YARATISH FUNKSIYASI ---
def unique_slugify(instance, value, slug_field_name='slug', queryset=None):
    slug = slugify(value)
    if queryset is None:
        queryset = instance.__class__.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    original_slug = slug
    for i in itertools.count(1):
        if not queryset.filter(**{slug_field_name: slug}).exists():
            break
        slug = f"{original_slug}-{i}"
    return slug


# --- KATEGORIYA MODELI ---
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


# --- ASAR MODELI ---
class Artwork(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artworks')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    contact = models.CharField(max_length=255)
    telegram = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Telegram manzili (ixtiyoriy)"
    )
    image = models.ImageField(upload_to='artworks/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='artworks')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title)
        # Telegram manzilini avtomatik to‘g‘rilash
        if self.telegram:
            self.telegram = self.telegram.strip()
            if not self.telegram.startswith('@') and 't.me/' not in self.telegram:
                self.telegram = '@' + self.telegram
        super().save(*args, **kwargs)

    @property
    def first_image_url(self):
        """Agar asosiy image yo‘q bo‘lsa, bog‘langan ArtworkImage dan birinchi rasmni qaytaradi."""
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        if hasattr(self, 'images') and self.images.exists():
            first_img = self.images.first()
            if first_img and first_img.image:
                try:
                    return first_img.image.url
                except Exception:
                    pass
        return None


# --- RASM YO‘NALISHI FUNKSIYASI ---
def artwork_image_upload_to(instance: 'ArtworkImage', filename: str):
    return f"artworks/{timezone.now().strftime('%Y/%m')}/{filename}"


# --- KO‘P RASMLI MODEL ---
class ArtworkImage(models.Model):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=artwork_image_upload_to)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.artwork.title}"


# --- REYTING MODELI ---
class Rating(models.Model):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('artwork', 'user')

    def __str__(self):
        return f"{self.artwork} - {self.value} by {self.user}"


# --- IZOH MODELI ---
class Comment(models.Model):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"Comment by {self.user} on {self.artwork}"


# --- KO‘RISHLAR MODELI ---
class ArtworkView(models.Model):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='artwork_views')
    ip_address = models.CharField(max_length=45, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['artwork', 'user', 'ip_address', 'created'])]

    def __str__(self):
        who = self.user.username if self.user else self.ip_address
        return f"View {self.artwork} by {who}"
