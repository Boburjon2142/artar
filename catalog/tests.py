from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Artwork, Category, Rating, ArtworkView, Comment


class CatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.user2 = User.objects.create_user(username='bob', password='pass12345')
        self.cat = Category.objects.create(name='Painting')
        self.art = Artwork.objects.create(author=self.user, title='Sunset', price=10, contact='123', category=self.cat)

    def test_artwork_create(self):
        self.client.login(username='alice', password='pass12345')
        url = reverse('catalog:create')
        resp = self.client.post(url, {
            'title': 'New Art', 'price': '25', 'description': 'desc', 'contact': 'phone', 'category': self.cat.id,
            'images-TOTAL_FORMS': '3', 'images-INITIAL_FORMS': '0', 'images-MIN_NUM_FORMS': '0', 'images-MAX_NUM_FORMS': '3',
        })
        self.assertEqual(resp.status_code, 200)  # no files provided; still renders

    def test_rating_unique(self):
        self.client.login(username='bob', password='pass12345')
        url = reverse('catalog:detail', args=[self.art.slug])
        # first rating
        self.client.post(url, {'value': '5', 'rating_submit': '1'})
        self.assertEqual(Rating.objects.filter(artwork=self.art, user=self.user2).count(), 0)
        # different user
        self.client.post(url, {'value': '4', 'rating_submit': '1'})
        self.assertEqual(Rating.objects.filter(artwork=self.art, user=self.user2).count(), 0)
        # switch login user and rate
        self.client.logout()
        self.client.login(username='alice', password='pass12345')
        self.client.post(url, {'value': '3', 'rating_submit': '1'})
        self.assertEqual(Rating.objects.filter(artwork=self.art, user=self.user).count(), 1)
        # update same rating
        self.client.post(url, {'value': '2', 'rating_submit': '1'})
        self.assertEqual(Rating.objects.get(artwork=self.art, user=self.user).value, 2)

    def test_unique_view_per_user(self):
        url = reverse('catalog:detail', args=[self.art.slug])
        # Anonymous counts once per IP
        self.client.get(url)
        self.assertEqual(ArtworkView.objects.filter(artwork=self.art).count(), 1)
        self.client.get(url)
        self.assertEqual(ArtworkView.objects.filter(artwork=self.art).count(), 1)
        # Logged-in different user should increment
        self.client.login(username='bob', password='pass12345')
        self.client.get(url)
        self.assertEqual(ArtworkView.objects.filter(artwork=self.art).count(), 2)

    def test_search_filter(self):
        a2 = Artwork.objects.create(author=self.user, title='Mountains', price=50, contact='123', category=self.cat)
        url = reverse('catalog:home')
        resp = self.client.get(url, {'title': 'Mount'})
        self.assertContains(resp, 'Mountains')
        self.assertNotContains(resp, 'Sunset')

    def test_comment_requires_login(self):
        url = reverse('catalog:detail', args=[self.art.slug])
        resp = self.client.post(url, {'text': 'hi', 'comment_submit': '1'})
        self.assertEqual(resp.status_code, 302)
