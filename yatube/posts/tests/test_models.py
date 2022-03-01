"""Тестирование моделей приложения posts."""
from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User

USER = 'AuthUser'
AUTHOR = 'PostAuthor'


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая группа',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = ModelsTest.post
        post_field_verboses = {
            'text': 'Текст записи',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in post_field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

        comment = ModelsTest.comment
        comment_field_verboses = {
            'post': 'Запись',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for field, expected_value in comment_field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_value
                )

        follow = ModelsTest.follow
        follow_field_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for field, expected_value in follow_field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = ModelsTest.post
        post_field_help_texts = {
            'text': 'Введите текст записи',
            'group': 'Группа, к которой относится запись',
        }
        for field, expected_value in post_field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )

        comment = ModelsTest.comment
        comment_field_help_texts = {
            'post': 'Запись, к которой относится комментарий',
            'text': 'Введите текст комментария',
        }
        for field, expected_value in comment_field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text,
                    expected_value
                )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = ModelsTest.post
        post_name = post.text

        comment = ModelsTest.comment
        comment_name = comment.text

        follow = ModelsTest.follow
        follow_name = f'{USER} подписан на {AUTHOR}.'

        object_names = {
            post_name: str(post),
            comment_name: str(comment),
            follow_name: str(follow),
        }
        for object_name, str_view in object_names.items():
            self.assertEqual(object_name, str_view)
