from django.contrib import admin
from .models import Artwork, ArtworkImage, Rating, Comment, Category


class ArtworkImageInline(admin.TabularInline):
    model = ArtworkImage
    extra = 1


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'price', 'created')
    list_filter = ('category', 'created')
    search_fields = ('title', 'author__username')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ArtworkImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('artwork', 'user', 'value', 'created')
    list_filter = ('value',)
    search_fields = ('artwork__title', 'user__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('artwork', 'user', 'created')
    list_filter = ('created',)
    search_fields = ('artwork__title', 'user__username', 'text')

