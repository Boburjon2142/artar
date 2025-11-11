from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from .models import ArtworkImage, Artwork

def compress_image(image_path):
    try:
        img = Image.open(image_path)
        img.convert('RGB').save(image_path, quality=70, optimize=True)
    except Exception:
        pass

@receiver(post_save, sender=Artwork)
def compress_artwork_main(sender, instance, **kwargs):
    if instance.image:
        compress_image(instance.image.path)

@receiver(post_save, sender=ArtworkImage)
def compress_artwork_images(sender, instance, **kwargs):
    if instance.image:
        compress_image(instance.image.path)
