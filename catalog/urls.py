from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('art/create/', views.art_create, name='create'),
    path('art/<slug:slug>/edit/', views.art_update, name='update'),
    path('art/<slug:slug>/delete/', views.art_delete, name='delete'),
    path('art/<slug:slug>/', views.art_detail, name='detail'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
]
