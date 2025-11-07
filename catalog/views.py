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
        arts = list(qs.order_by('-created')[:12])
        has_more = qs.count() > 12
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
from django.core.paginator import Paginator
from django.shortcuts import render
from django.apps import apps
from django.db import models
from django.forms import ModelForm
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse, NoReverseMatch


def _get_model(app_label: str, candidates):
    for name in candidates:
        try:
            return apps.get_model(app_label, name)
        except LookupError:
            continue
    return None


def home_view(request):
    # Resolve primary listing model dynamically to avoid import errors
    Listing = _get_model('catalog', [
        'Art', 'Artwork', 'ArtItem', 'Product', 'Item', 'Listing', 'Ad', 'Announcement', 'Elon'
    ])
    Category = _get_model('catalog', ['Category', 'ArtCategory', 'ProductCategory'])

    if Listing is None:
        # Render graceful message rather than crash
        return render(request, 'catalog/home.html', {
            'page_obj': Paginator([], 12).get_page(1),
            'categories': Category.objects.all() if Category else [],
        })

    qs = Listing.objects.all()

    # Determine available fields
    field_names = {f.name for f in Listing._meta.get_fields() if isinstance(f, models.Field)}

    # Default ordering: newest by id or created fields
    if 'id' in field_names:
        qs = qs.order_by('-id')
    elif 'created_at' in field_names:
        qs = qs.order_by('-created_at')
    elif 'date' in field_names:
        qs = qs.order_by('-date')

    params = request.GET

    # Title filter
    title = params.get('title')
    if title:
        if 'title' in field_names:
            qs = qs.filter(title__icontains=title)
        elif 'name' in field_names:
            qs = qs.filter(name__icontains=title)

    # Category by slug if FKey named category and related has slug
    cat = params.get('category')
    if cat and 'category' in field_names:
        try:
            rel = Listing._meta.get_field('category').remote_field.model
            rel_fields = {f.name for f in rel._meta.get_fields() if isinstance(f, models.Field)}
            if 'slug' in rel_fields:
                qs = qs.filter(category__slug=cat)
            elif 'id' in rel_fields:
                qs = qs.filter(category__id=cat)
        except Exception:
            pass

    # Price bounds
    mn = params.get('min_price')
    if mn:
        for pfield in ('price', 'amount', 'cost'):
            if pfield in field_names:
                qs = qs.filter(**{f'{pfield}__gte': mn})
                break

    mx = params.get('max_price')
    if mx:
        for pfield in ('price', 'amount', 'cost'):
            if pfield in field_names:
                qs = qs.filter(**{f'{pfield}__lte': mx})
                break

    # Order by if provided and allowed
    order = params.get('order_by')
    if order:
        # Map friendly keys to actual fields
        mapping = {
            '-date': '-date' if 'date' in field_names else '-created_at' if 'created_at' in field_names else '-id',
            'price': 'price' if 'price' in field_names else 'amount' if 'amount' in field_names else None,
            '-price': '-price' if 'price' in field_names else '-amount' if 'amount' in field_names else None,
            '-rating': '-avg_rating' if 'avg_rating' in field_names else '-rating' if 'rating' in field_names else None,
        }
        target = mapping.get(order, order)
        if target and target.lstrip('-') in field_names:
            qs = qs.order_by(target)

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all() if Category else [],
    }

    return render(request, 'catalog/home.html', context)


# -----------------------------
# Create view (catalog:create)
# -----------------------------

def create_view(request):
    """Create listing using dynamic ModelForm and optional image formset.

    - Works with models named: Art/Artwork/ArtItem/Product/Item/Listing/Ad/Announcement/Elon
    - Tries to detect fields: title/name, price/amount, contact/phone, category, description/text/content
    - If there is a related images model with FK to listing and an ImageField named 'image', it exposes a formset
    """
    Listing = _get_model('catalog', [
        'Art', 'Artwork', 'ArtItem', 'Product', 'Item', 'Listing', 'Ad', 'Announcement', 'Elon'
    ])
    if Listing is None:
        return render(request, 'catalog/create.html', {'form': None, 'image_formset': None})

    # Detect common fields
    fset = {f.name: f for f in Listing._meta.get_fields() if isinstance(f, models.Field)}
    possible = {
        'title': next((n for n in ['title', 'name'] if n in fset), None),
        'price': next((n for n in ['price', 'amount', 'cost'] if n in fset), None),
        'contact': next((n for n in ['contact', 'phone', 'contact_phone'] if n in fset), None),
        'category': 'category' if 'category' in fset else None,
        'description': next((n for n in ['description', 'text', 'content'] if n in fset), None),
        'slug': 'slug' if 'slug' in fset else None,
    }

    form_fields = [n for n in [possible['title'], possible['price'], possible['contact'], possible['category'], possible['description']] if n]

    class ListingForm(ModelForm):
        class Meta:
            model = Listing
            fields = form_fields if form_fields else '__all__'

    # Detect author field
    author_field = _author_field(Listing)

    # Detect images related model
    ImagesModel = None
    image_field_name = None
    order_field_name = None
    fk_name = None
    for rel in Listing._meta.get_fields():
        if getattr(rel, 'is_relation', False) and getattr(rel, 'one_to_many', False):
            rm = rel.related_model
            if not rm:
                continue
            rm_fields = {f.name: f for f in rm._meta.get_fields() if isinstance(f, models.Field)}
            img_name = next((n for n, f in rm_fields.items() if n in ['image', 'file'] and f.get_internal_type() in ['ImageField', 'FileField']), None)
            if img_name:
                ImagesModel = rm
                image_field_name = img_name
                order_field_name = 'order' if 'order' in rm_fields else None
                fk_name = rel.field.name if hasattr(rel, 'field') else rel.remote_field.name
                break

    ImageFormSet = None
    if ImagesModel and fk_name and image_field_name:
        fields = [image_field_name]
        if order_field_name:
            fields.append(order_field_name)
        ImageFormSet = inlineformset_factory(Listing, ImagesModel, fields=fields, extra=3, can_delete=True)

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES, prefix='images') if ImageFormSet else None
        if form.is_valid() and (formset is None or formset.is_valid()):
            instance = form.save(commit=False)
            if author_field and getattr(request, 'user', None) and request.user.is_authenticated:
                try:
                    setattr(instance, author_field, request.user)
                except Exception:
                    pass
            instance.save()
            if formset:
                fsi = formset.save(commit=False)
                for img in fsi:
                    try:
                        setattr(img, fk_name, instance)
                        img.save()
                    except Exception:
                        continue
                # handle deletions
                for obj in formset.deleted_objects:
                    try:
                        obj.delete()
                    except Exception:
                        pass
            # Redirect to detail if possible
            try:
                if possible['slug']:
                    url = reverse('catalog:detail', args=[getattr(instance, possible['slug'])])
                else:
                    url = reverse('catalog:detail', args=[instance.pk])
                return HttpResponseRedirect(url)
            except NoReverseMatch:
                return HttpResponseRedirect(reverse('catalog:home'))
        else:
            context = {'form': form, 'image_formset': formset}
            return render(request, 'catalog/create.html', context)
    else:
        form = ListingForm()
        formset = ImageFormSet(prefix='images') if ImageFormSet else None
        context = {'form': form, 'image_formset': formset}
        return render(request, 'catalog/create.html', context)
