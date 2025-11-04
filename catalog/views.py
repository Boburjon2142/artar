from __future__ import annotations
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import Artwork, Category, Rating, Comment, ArtworkView
from .forms import ArtworkForm, ArtworkImageFormSet, RatingForm, CommentForm


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def home_view(request):
    qs = Artwork.objects.select_related('author', 'category').prefetch_related('images').annotate(
        avg_rating=Avg('ratings__value'),
        views_count=Count('views'),
    )

    title = request.GET.get('title', '').strip()
    category = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    rating_gte = request.GET.get('rating_gte', '').strip()
    order_by = request.GET.get('order_by', '').strip()

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

    allowed_order = {
        'price': 'price',
        '-price': '-price',
        'rating': 'avg_rating',
        '-rating': '-avg_rating',
        'date': '-created',
        '-date': 'created',
    }
    if order_by in allowed_order:
        qs = qs.order_by(allowed_order[order_by])

    show_all = request.GET.get('all') == '1'
    page_obj = None
    arts = None
    has_more = False
    see_all_url = None

    if show_all:
        paginator = Paginator(qs, 9)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        arts = list(qs.order_by('-created')[:10])
        has_more = qs.count() > 10
        params = request.GET.copy()
        params['all'] = '1'
        see_all_url = f"?{params.urlencode()}"

    categories = Category.objects.all()
    ctx = {
        'page_obj': page_obj,
        'arts': arts,
        'has_more': has_more,
        'see_all_url': see_all_url,
        'categories': categories,
        'filters': {
            'title': title, 'category': category, 'min_price': min_price,
            'max_price': max_price, 'rating_gte': rating_gte, 'order_by': order_by
        }
    }
    return render(request, 'catalog/home.html', ctx)


def art_detail(request, slug):
    art = get_object_or_404(
        Artwork.objects.select_related('author', 'category').prefetch_related('images', 'comments__user'),
        slug=slug
    )

    # Unique view counting: +1 only for a new viewer (per user or IP once)
    user = request.user if request.user.is_authenticated else None
    ip = get_client_ip(request)
    if user:
        if not ArtworkView.objects.filter(artwork=art, user=user).exists():
            ArtworkView.objects.create(artwork=art, user=user, ip_address=ip)
    else:
        if not ArtworkView.objects.filter(artwork=art, user__isnull=True, ip_address=ip).exists():
            ArtworkView.objects.create(artwork=art, user=None, ip_address=ip)

    avg_rating = art.ratings.aggregate(r=Avg('value'))['r'] or 0
    views_count = art.views.count()

    if request.method == 'POST':
        if 'rating_submit' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Reyting berish uchun login qiling.')
                return redirect('login')
            form = RatingForm(request.POST)
            if form.is_valid():
                value = form.cleaned_data['value']
                obj, created = Rating.objects.update_or_create(
                    artwork=art, user=request.user, defaults={'value': value}
                )
                messages.success(request, 'Reyting saqlandi.')
                return redirect('catalog:detail', slug=art.slug)
        elif 'comment_submit' in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, 'Izoh qoldirish uchun login qiling.')
                return redirect('login')
            cform = CommentForm(request.POST)
            if cform.is_valid():
                Comment.objects.create(artwork=art, user=request.user, text=cform.cleaned_data['text'])
                messages.success(request, 'Izoh qo‘shildi.')
                return redirect('catalog:detail', slug=art.slug)

    rating_form = RatingForm()
    comment_form = CommentForm()

    # Simple pagination for comments
    comments_qs = art.comments.select_related('user')
    paginator = Paginator(comments_qs, 10)
    page_number = request.GET.get('cpage')
    comments_page = paginator.get_page(page_number)

    ctx = {
        'art': art,
        'avg_rating': avg_rating,
        'views_count': views_count,
        'rating_form': rating_form,
        'comment_form': comment_form,
        'comments_page': comments_page,
    }
    return render(request, 'catalog/detail.html', ctx)


@login_required
def art_create(request):
    if request.method == 'POST':
        form = ArtworkForm(request.POST)
        formset = ArtworkImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            art = form.save(commit=False)
            art.author = request.user
            art.save()
            formset.instance = art
            images_count = 0
            for f in formset.save(commit=False):
                images_count += 1
                f.save()
            if images_count > 3:
                messages.error(request, 'Eng ko‘pi 3 ta rasm yuklang.')
                art.delete()
            else:
                messages.success(request, 'E’lon yaratildi.')
                return redirect('catalog:detail', slug=art.slug)
    else:
        form = ArtworkForm()
        formset = ArtworkImageFormSet()

    return render(request, 'catalog/form.html', {'form': form, 'formset': formset, 'is_create': True})


@login_required
def art_update(request, slug):
    art = get_object_or_404(Artwork, slug=slug)
    if art.author != request.user:
        messages.error(request, 'Faqat muallif tahrirlashi mumkin.')
        return redirect('catalog:detail', slug=art.slug)

    if request.method == 'POST':
        form = ArtworkForm(request.POST, instance=art)
        formset = ArtworkImageFormSet(request.POST, request.FILES, instance=art)
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save()
            if art.images.count() > 3:
                messages.error(request, 'Eng ko‘pi 3 ta rasm.')
            else:
                messages.success(request, 'E’lon yangilandi.')
                return redirect('catalog:detail', slug=art.slug)
    else:
        form = ArtworkForm(instance=art)
        formset = ArtworkImageFormSet(instance=art)

    return render(request, 'catalog/form.html', {'form': form, 'formset': formset, 'is_create': False})


@login_required
def art_delete(request, slug):
    art = get_object_or_404(Artwork, slug=slug)
    if art.author != request.user:
        messages.error(request, 'Faqat muallif o‘chira oladi.')
        return redirect('catalog:detail', slug=art.slug)

    if request.method == 'POST':
        art.delete()
        messages.success(request, 'E’lon o‘chirildi.')
        return redirect('catalog:home')

    return render(request, 'catalog/delete_confirm.html', {'art': art})
