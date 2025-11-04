import io
import random
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import transaction
from catalog.models import Category, Artwork, ArtworkImage, Comment, Rating


def tiny_png_bytes(color=(200, 200, 200)):
    # 1x1 PNG (hardcoded binary for simplicity)
    return (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\xdac``\x00\x00\x00\x04\x00\x01"
            b"\x0b\x0c\x02\x7f\x00\x00\x00\x00IEND\xaeB`\x82")


class Command(BaseCommand):
    help = 'Seed demo data: categories, users, artworks with images, comments, ratings.'

    @transaction.atomic
    def handle(self, *args, **options):
        cats = ['Rasm', 'Haykaltaroshlik', 'Grafika', 'Foto', 'Raqamli']
        categories = []
        for c in cats:
            cat, _ = Category.objects.get_or_create(name=c)
            categories.append(cat)

        users = []
        for i in range(1, 4):
            u, created = User.objects.get_or_create(username=f'demo{i}')
            if created:
                u.set_password('password')
                u.save()
            users.append(u)

        for i in range(1, 21):
            author = random.choice(users)
            title = f"Demo asar {i}"
            art, _ = Artwork.objects.get_or_create(
                author=author,
                title=title,
                defaults={
                    'price': random.randint(10, 500),
                    'description': 'Demo ta’rif',
                    'contact': '+998 90 000 00 00',
                    'category': random.choice(categories)
                }
            )
            for j in range(random.randint(1, 3)):
                img_content = ContentFile(tiny_png_bytes(), name=f'demo_{i}_{j}.png')
                ArtworkImage.objects.create(artwork=art, image=img_content, order=j)

            # add ratings and comments
            for u in users:
                Rating.objects.update_or_create(artwork=art, user=u, defaults={'value': random.randint(3, 5)})
                Comment.objects.create(artwork=art, user=u, text='Zo‘r asar!')

        self.stdout.write(self.style.SUCCESS('Demo ma’lumotlar yaratildi.'))

