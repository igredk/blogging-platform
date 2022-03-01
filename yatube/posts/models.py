from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import CheckConstraint, UniqueConstraint, Q, F

User = get_user_model()


class Post(models.Model):
    text = models.TextField('Текст записи', help_text='Введите текст записи')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        "Group",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='group',
        verbose_name='Группа',
        help_text='Группа, к которой относится запись'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name_plural = 'Записи'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField('Группа', max_length=200)
    slug = models.SlugField('Код группы', max_length=20, unique=True)
    description = models.TextField('Описание группы')

    class Meta:
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запись',
        help_text='Запись, к которой относится комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )
    created = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Комментарии'
        ordering = ('-created',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        constraints = (
            CheckConstraint(check=~Q(user=F('author')), name='no_self_follow'),
            UniqueConstraint(fields=('user', 'author'),
                             name='unique_followers'
                             )
        )
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}.'
