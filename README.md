# ARTAR — Django Art Catalog

Talablar bo‘yicha to‘liq ishlaydigan Django loyiha: Postgres bilan ishlaydi, mobilga mos UI, e’lonlar cardlari, detailda reyting/izoh/unique-ko‘rishlar, profil kuzatish, admin boshqaruvi, seed komanda va unit testlar bilan.

## O‘rnatish va ishga tushirish

```
python -m venv .venv && .venv\\Scripts\\activate    # Windows
# macOS/Linux: python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# macOS/Linux: cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ixtiyoriy demo ma’lumotlar:

```
python manage.py seed_demo
```

## Xususiyatlar

- ArtworkCreateView: 3 ta rasm cheklovi, sarlavha, narx, ta’rif, aloqa, kategoriya
- Muallif faqat o‘z e’lonini tahrir/qayta yuklay oladi
- Profil (dashboard): foydalanuvchi ma’lumotlarini tahrirlash, o‘zi yuklagan asarlar metrikalari (views_count, o‘rtacha rating, izohlar soni), yangi izohlar oqimi
- Admin panel: Artwork, ArtworkImage, Rating, Comment, Category, Profile ro‘yxatdan o‘tgan; qidirish, filterlar, inlines (ArtworkImageInline)
- Templateler (Bootstrap 5): base, home, detail, form, login/register/profile_edit/dashboard
- Viewlar: home filter + annotate Avg('rating__value'), order_by, paginate; art_detail: unique view 12 soat; rating create/update; comment create; art_create/update/delete: login required + author check; profile_dashboard; profile_edit
- Formlar: ArtworkForm, ArtworkImage formset (max 3), narx musbat, aloqa bo‘sh bo‘lmasin
- Xavfsizlik: CSRF yoqilgan; upload_to='artworks/%Y/%m/'; slug autocreate + unikallik
- Performance: select_related, prefetch_related ishlatiladi
- Testlar: Artwork create, rating unique, unique view 12 soat, search/filter, comment login required

## Ijtimoiy tarmoqlar

- Telegram: https://t.me/artar_uz
- Instagram: https://www.instagram.com/artar_uz
- YouTube: https://www.youtube.com/@artar_uz

Facebook ikonkasi olib tashlangan.

## Deploy (Gunicorn + Whitenoise)

1) .env ni ishlab chiqarish uchun to‘ldiring:

```
DEBUG=0
ALLOWED_HOSTS=your.domain.com,www.your.domain.com
CSRF_TRUSTED_ORIGINS=https://your.domain.com,https://www.your.domain.com
SECURE_SSL_REDIRECT=1
```

2) Staticlarni yig‘ing:

```
python manage.py collectstatic --noinput
```

3) Gunicorn bilan ishga tushiring (reverse proxy orqasida):

```
pip install -r requirements.txt
gunicorn artar.wsgi --bind 0.0.0.0:8000
```

Nginx orqali `proxy_set_header X-Forwarded-Proto https;` yuboring, `ALLOWED_HOSTS` va `CSRF_TRUSTED_ORIGINS` ni to‘g‘ri sozlang. Whitenoise staticlarni bevosita Django orqali xizmat qiladi.
