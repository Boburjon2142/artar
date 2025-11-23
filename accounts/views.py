from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.contrib.auth import login

from .forms import RegistrationForm, ProfileForm
from catalog.models import Artwork, Comment


def register(request):
    """
    Yangi foydalanuvchi ro‘yxatdan o‘tishi
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Ro‘yxatdan o‘tish muvaffaqiyatli.')
            return redirect('accounts:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    """
    Foydalanuvchi shaxsiy kabineta: profil, e’lonlar, statistika
    """

    # === 1) Foydalanuvchiga tegishli e’lonlar (optimizatsiya bilan) ===
    arts = (
        Artwork.objects.filter(author=request.user)
        .annotate(
            views_count=Count('views'),             # Ko‘rishlar
            avg_rating=Avg('ratings__value'),       # O‘rtacha reyting
            comments_count=Count('comments')        # Izohlar
        )
        .select_related('category')
        .prefetch_related('images')
        .order_by('-created')
    )

    # === 2) Izohlar (oxirgi 20 ta) ===
    comments = (
        Comment.objects.filter(artwork__author=request.user)
        .select_related('user', 'artwork')
        .order_by('-created')[:20]
    )

    # === 3) KATTALASHGAN STATISTIKA ===
    total_arts = arts.count()
    total_comments = comments.count()
    total_views = arts.aggregate(total=Sum('views_count'))['total'] or 0

    # Barcha reytinglar bo‘yicha umumiy o‘rtacha
    avg_rating = arts.aggregate(avg=Avg('avg_rating'))['avg'] or 0

    # DISTINCT kategoriyalar soni
    total_categories = arts.values('category').distinct().count()

    # === 4) Diagramma uchun barlar ===
    metrics = [
        ("E’lonlar", total_arts),
        ("Ko‘rishlar", total_views),
        ("Izohlar", total_comments),
        ("Reyting", round(avg_rating, 1)),
        ("Kategoriyalar", total_categories),
    ]

    max_val = max([v for _, v in metrics] + [1])

    stats_bars = [
        {
            'label': label,
            'value': value,
            'percent': int((value / max_val) * 100)
        }
        for label, value in metrics
    ]

    # === 5) Templatega kontekst ===
    ctx = {
        'arts': arts,
        'comments': comments,
        'total_arts': total_arts,
        'total_comments': total_comments,
        'total_views': total_views,
        'avg_rating': avg_rating,
        'stats_bars': stats_bars,
    }

    return render(request, 'accounts/dashboard.html', ctx)


@login_required
def profile_edit(request):
    """
    Profil ma’lumotlarini tahrirlash
    """
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil yangilandi.')
            return redirect('accounts:dashboard')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})
