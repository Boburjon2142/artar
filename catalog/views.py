from __future__ import annotations
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count

from .models import Artwork, Category, Rating, Comment, ArtworkView
from .forms import ArtworkForm, ArtworkImageFormSet, RatingForm, CommentForm


# 🧠 IP olish yordamchi funksiyasi
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '')


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

    # POST: Reyting & Izoh
    if request.method == 'POST':

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
        'comment_form': comment_form,
        'comments_page': comments_page,
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
    if request.method == 'POST':
        form = ArtworkForm(request.POST)
        formset = ArtworkImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
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
