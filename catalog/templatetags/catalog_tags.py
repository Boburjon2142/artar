from django import template
from catalog.models import Artwork, Rating, Comment

register = template.Library()

@register.simple_tag
def user_listing_stats(user):
    """Foydalanuvchiga tegishli statistikani qaytaradi."""

    arts = Artwork.objects.filter(author=user)

    total = arts.count()
    views = arts.aggregate(total_views=models.Sum("views_count"))["total_views"] or 0
    comments = Comment.objects.filter(artwork__in=arts).count()
    ratings = Rating.objects.filter(artwork__in=arts)

    if ratings.exists():
        avg_rating = round(ratings.aggregate(avg=models.Avg("value"))["avg"] or 0, 1)
    else:
        avg_rating = 0

    # Diagramma uchun barlar
    stats_bars = [
        {"label": "E’lonlar", "value": total, "percent": total * 10},
        {"label": "Ko‘rishlar", "value": views, "percent": min(100, views / 2)},
        {"label": "Izohlar", "value": comments, "percent": comments * 10},
        {"label": "Reyting", "value": avg_rating, "percent": avg_rating * 10},
    ]

    return {
        "total": total,
        "views": views,
        "comments": comments,
        "avg_rating": avg_rating,
        "bars": stats_bars,
    }
