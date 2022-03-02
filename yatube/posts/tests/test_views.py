"""Тестирование view-функций приложения posts."""
import shutil
import tempfile

from django import forms
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

MAIN_PAGE = reverse('posts:index')
MAIN_PAGE_TEMPLATE = 'posts/index.html'

SLUG = 'test_group'
GROUP_PAGE = reverse('posts:group_list', kwargs={'slug': SLUG})
GROUP_PAGE_TEMPLATE = 'posts/group_list.html'

AUTH_USER = 'AuthUser'
AUTHOR = 'PostAuthor'
AUTHOR_PAGE = reverse('posts:profile', kwargs={'username': AUTHOR})
AUTHOR_PAGE_TEMPLATE = 'posts/profile.html'

POST_CREATE_PAGE = reverse('posts:post_create')
POST_CREATE_PAGE_TEMPLATE = 'posts/create_post.html'

POST_PAGE_TEMPLATE = 'posts/post_detail.html'

FOLLOW_PAGE = reverse('posts:follow_index')
FOLLOW_PAGE_TEMPLATE = 'posts/follow.html'

FOLLOW = reverse('posts:profile_follow', kwargs={'username': AUTHOR})
UNFOLLOW = reverse('posts:profile_unfollow', kwargs={'username': AUTHOR})

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLNamesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.auth_user = User.objects.create_user(username=AUTH_USER)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание'
        )
        test_image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись',
            group=cls.group,
            image=test_image,
        )
        cls.POST_PAGE = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_PAGE = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.clear = cache.clear()
        # Неавторизованный пользователь
        self.guest_client = Client()

        # Автор записи
        self.author = PostsURLNamesTests.author
        self.author_client = Client()
        self.author_client.force_login(self.author)

        # Авторизованный пользователь
        self.auth_user = PostsURLNamesTests.auth_user
        self.auth_user_client = Client()
        self.auth_user_client.force_login(self.auth_user)

    def test_url_names(self):
        """При обращении к name вызывается соответствующий HTML-шаблон."""
        templates_pages_names = {
            MAIN_PAGE: MAIN_PAGE_TEMPLATE,
            GROUP_PAGE: GROUP_PAGE_TEMPLATE,
            AUTHOR_PAGE: AUTHOR_PAGE_TEMPLATE,
            PostsURLNamesTests.POST_PAGE: POST_PAGE_TEMPLATE,
            PostsURLNamesTests.POST_EDIT_PAGE: POST_CREATE_PAGE_TEMPLATE,
            POST_CREATE_PAGE: POST_CREATE_PAGE_TEMPLATE,
            FOLLOW_PAGE: FOLLOW_PAGE_TEMPLATE,
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.guest_client.get(PostsURLNamesTests.POST_PAGE))
        self.assertEqual(
            response.context.get('post').author,
            PostsURLNamesTests.author
        )
        self.assertEqual(
            response.context.get('post').text,
            PostsURLNamesTests.post.text
        )
        self.assertEqual(
            response.context.get('post').group,
            PostsURLNamesTests.group
        )
        self.assertEqual(
            response.context.get('post').image,
            PostsURLNamesTests.post.image
        )

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(POST_CREATE_PAGE)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        # Типы полей формы в словаре context соответствуют ожидаемым.
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.author_client.get(PostsURLNamesTests.POST_EDIT_PAGE))
        self.assertEqual(
            response.context.get('form')['text'].value(),
            PostsURLNamesTests.post.text
        )
        self.assertEqual(response.context.get('form')['group'].value(), 1)

    def test_index_page_cache_check(self):
        """Проверка кэширования объектов страницы index."""
        first_call = self.guest_client.get(MAIN_PAGE)
        first_call_content = first_call.content
        first_call.context['page_obj'][0].delete()

        form_data = {
            'text': 'Кэширование',
        }
        self.author_client.post(POST_CREATE_PAGE, data=form_data, follow=True)

        second_call = self.guest_client.get(MAIN_PAGE)
        second_call_content = second_call.content
        self.assertEqual(first_call_content, second_call_content)

        cache.clear()

        third_call = self.guest_client.get(MAIN_PAGE)
        third_call_content = third_call.content
        self.assertNotEqual(second_call_content, third_call_content)

    def test_subscriptions(self):
        """Проверка подписки и отписки пользователя на(от) автора."""
        follows_count = Follow.objects.count()
        response = self.auth_user_client.get(FOLLOW)
        self.assertRedirects(response, FOLLOW_PAGE)
        self.assertEqual(Follow.objects.count(), follows_count + 1)

        response = self.auth_user_client.get(UNFOLLOW)
        self.assertRedirects(response, MAIN_PAGE)
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_subscriptions_context(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        posts_count = Post.objects.count()
        self.auth_user_client.get(FOLLOW)

        form_data = {
            'text': 'Подписка',
        }
        self.author_client.post(POST_CREATE_PAGE, data=form_data, follow=True)

        # Проверка количества записей на странице для подписчика.
        response = self.auth_user_client.get(FOLLOW_PAGE)
        self.assertEqual(
            len(response.context['page_obj']),
            posts_count + 1
        )
        # Проверка содержимого новой записи на странице подписки.
        new_post = response.context['page_obj'][0]
        self.assertEqual(
            new_post.text,
            form_data['text']
        )

        # Проверка количества записей на странице для не подписчика.
        response = self.author_client.get(FOLLOW_PAGE)
        self.assertEqual(
            len(response.context['page_obj']),
            posts_count - 1
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание'
        )
        cls.NUMBER_OF_POSTS = 13
        for i in range(1, cls.NUMBER_OF_POSTS + 1):
            paginator_image = SimpleUploadedFile(
                name=f'small_{i}.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            )
            cls.post = Post.objects.create(
                author=cls.author,
                text=f'Тестовая запись {i}',
                group=cls.group,
                image=paginator_image,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.clear = cache.clear()
        # Неавторизованный пользователь
        self.guest_client = Client()

    def test_paginator_pages(self):
        """Paginator выводит правильное количество записей
        на первой и второй странице.
        Проверка содержимого первой записи на каждой странице.
        """
        paginator_limit = 10
        url_names = (MAIN_PAGE, GROUP_PAGE, AUTHOR_PAGE)
        for address in url_names:
            response = self.guest_client.get(address)
            # Проверка количества записей на первой странице.
            self.assertEqual(
                len(response.context['page_obj']),
                paginator_limit
            )
            # Проверка содержимого первой записи страницы.
            first_post = response.context['page_obj'][0]
            post_author_0 = first_post.author
            post_text_0 = first_post.text
            post_group_0 = first_post.group
            post_image_0 = first_post.image
            self.assertEqual(post_author_0, PaginatorViewsTest.author)
            self.assertEqual(
                post_text_0,
                f'Тестовая запись {self.NUMBER_OF_POSTS}'
            )
            self.assertEqual(post_group_0, PaginatorViewsTest.group)
            self.assertEqual(
                post_image_0,
                f'posts/small_{self.NUMBER_OF_POSTS}.gif'
            )
            # Проверка количества записей на второй странице.
            response = self.client.get(address + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']),
                self.NUMBER_OF_POSTS % paginator_limit
            )
            # Проверка содержимого первой записи второй страницы.
            first_post = response.context['page_obj'][0]
            post_author_0 = first_post.author
            post_text_0 = first_post.text
            post_group_0 = first_post.group
            post_image_0 = first_post.image
            self.assertEqual(post_author_0, PaginatorViewsTest.author)
            self.assertEqual(
                post_text_0,
                f'Тестовая запись {self.NUMBER_OF_POSTS % paginator_limit}'
            )
            self.assertEqual(post_group_0, PaginatorViewsTest.group)
            self.assertEqual(
                post_image_0,
                f'posts/small_{self.NUMBER_OF_POSTS % paginator_limit}.gif'
            )
