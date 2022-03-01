from django.contrib import admin

from .models import Comment, Follow, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    # Добавляем возможность изменения group прямо в списке записей
    list_editable = ('group',)
    # Добавляем интерфейс для поиска по тексту записей
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = (
        'text',
        'created',
        'author',
        'post',
    )
    # Добавляем интерфейс для поиска по тексту комментариев
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('created',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = (
        'user',
        'author',
    )
    # Добавляем возможность изменения author прямо в списке подписок
    list_editable = ('author',)
