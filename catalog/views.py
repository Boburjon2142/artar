from __future__ import annotations
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.conf import settings
from django.urls import reverse
import urllib.request
import urllib.parse
import json
import logging

from .models import Artwork, Category, Rating, Comment, ArtworkView
from .forms import ArtworkForm, ArtworkImageFormSet, RatingForm, CommentForm
from .moderation import moderate_content
from .ai_content import analyze_content


logger = logging.getLogger(__name__)


# 🧠 IP olish yordamchi funksiyasi
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '')


def send_order_to_telegram(message: str) -> bool:
    """Minimal Telegram sendMessage helper without external deps."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        logger.warning("Telegram config missing: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False

    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        payload = json.dumps({'chat_id': chat_id, 'text': message})
        req = urllib.request.Request(
            url,
            data=payload.encode(),
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            ok = 200 <= getattr(resp, 'status', 500) < 300
            if not ok:
                logger.error("Telegram send failed with status %s", getattr(resp, 'status', 'unknown'))
            return ok
    except Exception as exc:
        logger.exception("Telegram order notification failed: %s", exc)
        return False


# 🏠 Bosh sahifa (TO‘LIQ TUZATILGAN)
def home_view(request):
    qs = Artwork.objects.select_related('author', 'category') \
        .prefetch_related('images') \
        .annotate(
            avg_rating=Avg('ratings__value'),
            views_count=Count('views'),
        )

    # Filtrlash parametrlari
    title = request.GET.get('title', '').strip()
    category = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    rating_gte = request.GET.get('rating_gte', '').strip()
    order_by = request.GET.get('order_by', '').strip()

    # Filter amallari
    if title:
        qs = qs.filter(title__icontains=title)
    if category:
        qs = qs.filter(category__slug=category)
    if min_price:
        qs = qs.filter(price__gte=min_price)
    if max_price:
        qs = qs.filter(price__lte=max_price)
    if rating_gte:
        qs = qs.filter(avg_rating__gte=rating_gte)

    # Tartiblash
    allowed_order = {
        'price': 'price',
        '-price': '-price',
        'rating': 'avg_rating',
        '-rating': '-avg_rating',
        'date': '-created',
        '-date': 'created',
    }
    qs = qs.order_by(allowed_order.get(order_by, '-created'))

    # PAGINATION — HAR DOIM SERVER-SIDE
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    ctx = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'filters': {
            'title': title,
            'category': category,
            'min_price': min_price,
            'max_price': max_price,
            'rating_gte': rating_gte,
            'order_by': order_by,
        },
    }

    return render(request, 'catalog/home.html', ctx)


# 🎨 Detal sahifa
def art_detail(request, slug):
    art = get_object_or_404(
        Artwork.objects.select_related('author', 'category')
        .prefetch_related('images', 'comments__user'),
        slug=slug
    )

    is_owner = request.user.is_authenticated and request.user == art.author

    # Ko‘rish logi
    ip = get_client_ip(request)
    if request.user.is_authenticated:
        if not ArtworkView.objects.filter(artwork=art, user=request.user).exists():
            ArtworkView.objects.create(artwork=art, user=request.user, ip_address=ip)
    else:
        if not ArtworkView.objects.filter(artwork=art, user__isnull=True, ip_address=ip).exists():
            ArtworkView.objects.create(artwork=art, user=None, ip_address=ip)

    avg_rating = art.ratings.aggregate(r=Avg('value'))['r'] or 0
    views_count = art.views.count()

    ai_suggestions = {}
    lang = request.GET.get('lang') or getattr(request, 'LANGUAGE_CODE', 'en') or 'en'
    if settings.OPENAI_API_KEY:
        images_bytes = []

        def _read_file(file_field):
            try:
                with file_field.open('rb') as fp:
                    return fp.read()
            except Exception:
                return None

        if art.image:
            data = _read_file(art.image)
            if data:
                images_bytes.append(data)

        for img in art.images.all()[:2]:
            if img.image:
                data = _read_file(img.image)
                if data:
                    images_bytes.append(data)

        try:
            ai_suggestions = analyze_content(
                art.title or '',
                art.description or '',
                images_bytes,
                target_lang=lang,
            ) or {}
        except Exception:
            ai_suggestions = {}

    # POST: Reyting & Izoh
    if request.method == 'POST':

        # 🛒 Buyurtma tugmasi
        if 'order_submit' in request.POST:
            buyer = request.user if request.user.is_authenticated else None
            seller = art.author
            buyer_phone = getattr(getattr(buyer, 'profile', None), 'phone', '') if buyer else '-'
            seller_phone = getattr(getattr(seller, 'profile', None), 'phone', '') or '-'
            link = request.build_absolute_uri(reverse('catalog:detail', args=[art.slug]))

            msg = (
                "🛒 Yangi buyurtma\n"
                f"Asar: {art.title}\n"
                f"Havola: {link}\n"
                f"Buyurtmachi: {buyer.username if buyer else 'Anonim'}\n"
                f"Email: {buyer.email if buyer and buyer.email else '-'}\n"
                f"Telefon: {buyer_phone or '-'}\n"
                f"E'lon egasi: {seller.username}\n"
                f"Email: {seller.email or '-'}\n"
                f"Telefon: {seller_phone}\n"
            )

            send_order_to_telegram(msg)
            return redirect('catalog:detail', slug=slug)

        # ⭐ Reyting
        if 'rating_submit' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, "Reyting berish uchun login qiling.")
                return redirect('login')

            form = RatingForm(request.POST)
            if form.is_valid():
                Rating.objects.update_or_create(
                    artwork=art,
                    user=request.user,
                    defaults={'value': form.cleaned_data['value']}
                )
                messages.success(request, "Reyting saqlandi.")
                return redirect('catalog:detail', slug=slug)

        # 💬 Izoh
        if 'comment_submit' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, "Izoh yozish uchun login qiling.")
                return redirect('login')

            cform = CommentForm(request.POST)
            if cform.is_valid():
                Comment.objects.create(
                    artwork=art,
                    user=request.user,
                    text=cform.cleaned_data['text']
                )
                messages.success(request, "Izoh qo‘shildi.")
                return redirect('catalog:detail', slug=slug)

    rating_form = RatingForm()
    user_rating = 0
    if request.user.is_authenticated:
        existing_rating = Rating.objects.filter(artwork=art, user=request.user).first()
        if existing_rating:
            user_rating = existing_rating.value
    comment_form = CommentForm()

    comments_qs = art.comments.select_related('user').order_by('-created')
    paginator = Paginator(comments_qs, 10)
    comments_page = paginator.get_page(request.GET.get('cpage'))

    ctx = {
        'art': art,
        'is_owner': is_owner,
        'avg_rating': avg_rating,
        'views_count': views_count,
        'rating_form': rating_form,
        'user_rating': user_rating,
        'star_range': [5, 4, 3, 2, 1],
        'comment_form': comment_form,
        'comments_page': comments_page,
        'ai_suggestions': ai_suggestions,
    }
    return render(request, 'catalog/detail.html', ctx)


# ❌ E’lon o‘chirish
@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if comment.user != request.user:
        messages.error(request, "Faqat o‘zingiz yozgan izohni o‘chirishingiz mumkin.")
        return redirect('catalog:detail', slug=comment.artwork.slug)

    if request.method == 'POST':
        art_slug = comment.artwork.slug
        comment.delete()
        messages.success(request, "Izoh o‘chirildi.")
        return redirect('catalog:detail', slug=art_slug)

    return render(request, 'catalog/delete_comment_confirm.html', {
        'comment': comment,
        'art': comment.artwork,
    })


# ➕ E'lon yaratish
@login_required
def art_create(request):
    ai_suggestions = {}

    if request.method == 'POST':
        form = ArtworkForm(request.POST)
        formset = ArtworkImageFormSet(request.POST, request.FILES)

        if 'ai_suggest' in request.POST:
            if not settings.OPENAI_API_KEY:
                messages.error(request, "AI suggestions unavailable (API key missing).")
            else:
                images_bytes = []
                for f in formset.forms:
                    img = f.files.get('image') if hasattr(f, 'files') else None
                    if img:
                        data = img.read()
                        img.seek(0)
                        images_bytes.append(data)
                try:
                    ai_suggestions = analyze_content(
                        form.data.get('title', ''),
                        form.data.get('description', ''),
                        images_bytes,
                    )
                    if ai_suggestions:
                        messages.info(request, "AI suggestions generated.")
                    else:
                        messages.warning(request, "AI suggestions unavailable right now. Please try again later.")
                except Exception as exc:
                    logger.exception("AI suggest failed: %s", exc)
                    messages.error(request, "AI suggestions failed. Please try again later.")
            return render(request, 'catalog/form.html', {
                'form': form,
                'formset': formset,
                'is_create': True,
                'ai_suggestions': ai_suggestions,
            })

        if form.is_valid() and formset.is_valid():
            images_bytes = []
            for f in formset.forms:
                img = f.cleaned_data.get('image') if hasattr(f, 'cleaned_data') else None
                if img:
                    data = img.read()
                    img.seek(0)
                    images_bytes.append(data)

            ok, reason = moderate_content(
                form.cleaned_data.get('title', ''),
                form.cleaned_data.get('description', ''),
                images_bytes,
                Artwork.objects.values_list('title', flat=True),
            )
            if not ok:
                messages.error(request, reason)
                return render(request, 'catalog/form.html', {
                    'form': form,
                    'formset': formset,
                    'is_create': True,
                })

            art = form.save(commit=False)
            art.author = request.user
            art.save()

            formset.instance = art
            formset.save()

            messages.success(request, "E’lon yaratildi.")
            return redirect('catalog:detail', slug=art.slug)

    else:
        form = ArtworkForm()
        formset = ArtworkImageFormSet()

    return render(request, 'catalog/form.html', {
        'form': form,
        'formset': formset,
        'is_create': True,
        'ai_suggestions': ai_suggestions,
    })


# ✏️ E'lon tahrirlash
@login_required
def art_update(request, slug):
    art = get_object_or_404(Artwork, slug=slug)

    if art.author != request.user:
        messages.error(request, "Faqat muallif tahrirlashi mumkin.")
        return redirect('catalog:detail', slug=slug)

    if request.method == 'POST':
        form = ArtworkForm(request.POST, instance=art)
        formset = ArtworkImageFormSet(request.POST, request.FILES, instance=art)

        if form.is_valid() and formset.is_valid():
            images_bytes = []
            for f in formset.forms:
                img = f.cleaned_data.get('image') if hasattr(f, 'cleaned_data') else None
                if img:
                    data = img.read()
                    img.seek(0)
                    images_bytes.append(data)

            ok, reason = moderate_content(
                form.cleaned_data.get('title', ''),
                form.cleaned_data.get('description', ''),
                images_bytes,
                Artwork.objects.exclude(pk=art.pk).values_list('title', flat=True),
            )
            if not ok:
                messages.error(request, reason)
                return render(request, 'catalog/form.html', {
                    'form': form,
                    'formset': formset,
                    'is_create': False,
                })

            form.save()
            formset.save()
            messages.success(request, "E’lon yangilandi.")
            return redirect('catalog:detail', slug=slug)

    else:
        form = ArtworkForm(instance=art)
        formset = ArtworkImageFormSet(instance=art)

    return render(request, 'catalog/form.html', {
        'form': form,
        'formset': formset,
        'is_create': False,
    })


# ❌ E'lon o‘chirish
@login_required
def art_delete(request, slug):
    art = get_object_or_404(Artwork, slug=slug)

    if art.author != request.user:
        messages.error(request, "Faqat muallif o‘chira oladi.")
        return redirect('catalog:detail', slug=slug)

    if request.method == 'POST':
        art.delete()
        messages.success(request, "E’lon o‘chirildi.")
        return redirect('catalog:home')

    return render(request, 'catalog/delete_confirm.html', {'art': art})
