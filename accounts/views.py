from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.contrib.auth import login

from .forms import RegistrationForm, ProfileForm
from catalog.models import Artwork, Comment


def register(request):
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
    arts = (
        Artwork.objects.filter(author=request.user)
        .annotate(
            views_count=Count('views'),
            avg_rating=Avg('ratings__value'),
            comments_count=Count('comments'),
        )
        .select_related('category')
        .prefetch_related('images')
        .order_by('-created')
    )

    # Latest comments on user's artworks
    comments = (
        Comment.objects.filter(artwork__author=request.user)
        .select_related('user', 'artwork')
        .order_by('-created')[:20]
    )
    # Metrics
    total_arts = arts.count()
    total_comments = comments.count()
    total_views = arts.aggregate(s=Sum('views_count'))['s'] or 0

    # Build simple bar chart data (normalized)
    metrics = [
        ("Asarlar", total_arts),
        ("Ko‘rishlar", total_views),
        ("Izohlar", total_comments),
        ("Reytinglar", int(arts.aggregate(r=Avg('avg_rating'))['r'] or 0)),
        ("Kategoriyalar", arts.values('category').distinct().count()),
    ]
    max_val = max([v for _, v in metrics] + [1])
    stats_bars = [{
        'label': label,
        'value': value,
        'percent': int((value / max_val) * 100) if max_val else 0
    } for label, value in metrics]

    ctx = {
        'arts': arts,
        'comments': comments,
        'total_arts': total_arts,
        'total_comments': total_comments,
        'total_views': total_views,
        'stats_bars': stats_bars,
    }

    return render(request, 'accounts/dashboard.html', ctx)


@login_required
def profile_edit(request):
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
