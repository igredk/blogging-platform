"""Тестирование путей и шаблонов приложения posts."""
from http import HTTPStatus

from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Group, Post, User

MAIN_PAGE = '/'
MAIN_PAGE_TEMPLATE = 'posts/index.html'

SLUG = 'test_group'
GROUP_PAGE = f'/group/{SLUG}/'
GROUP_PAGE_TEMPLATE = 'posts/group_list.html'

AUTHOR = 'PostAuthor'
AUTHOR_PAGE = f'/profile/{AUTHOR}/'
AUTHOR_PAGE_TEMPLATE = 'posts/profile.html'

POST_CREATE_PAGE = '/create/'
POST_CREATE_PAGE_TEMPLATE = 'posts/create_post.html'
POST_CREATE_REDIRECT = '/auth/login/?next=/create/'

POST_PAGE_TEMPLATE = 'posts/post_detail.html'

NONEXISTENT_PAGE = '/something/weird/page/'
NONEXISTENT_PAGE_TEMPLATE = 'core/404.html'


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.auth_user = User.objects.create_user(username='AuthUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись',
            group=cls.group
        )
        cls.POST_PAGE = f'/posts/{cls.post.id}/'
        cls.POST_EDIT_PAGE = f'/posts/{cls.post.id}/edit/'
        cls.POST_EDIT_REDIRECT =\
            f'/auth/login/?next=/posts/{cls.post.id}/edit/'
        cls.COMMENT_CREATE_PAGE = f'/posts/{cls.post.id}/comment/'
        cls.COMMENT_CREATE_REDIRECT =\
            f'/auth/login/?next=/posts/{cls.post.id}/comment/'

    def setUp(self):
        self.clear = cache.clear()
        # Неавторизованный пользователь
        self.guest_client = Client()

        # Автор записи
        self.author = PostsURLTests.author
        self.author_client = Client()
        self.author_client.force_login(self.author)

        # Авторизованный пользователь
        self.auth_user = PostsURLTests.auth_user
        self.auth_user_client = Client()
        self.auth_user_client.force_login(self.auth_user)

    def test_author_urls_templates(self):
        """Все страницы доступны авторизованному пользователю."""
        url_names = {
            MAIN_PAGE: MAIN_PAGE_TEMPLATE,
            GROUP_PAGE: GROUP_PAGE_TEMPLATE,
            AUTHOR_PAGE: AUTHOR_PAGE_TEMPLATE,
            PostsURLTests.POST_PAGE: POST_PAGE_TEMPLATE,
            PostsURLTests.POST_EDIT_PAGE: POST_CREATE_PAGE_TEMPLATE,
            POST_CREATE_PAGE: POST_CREATE_PAGE_TEMPLATE,
        }
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_anonymous_urls_templates(self):
        """Страницы доступны анонимному пользователю."""
        url_names = {
            MAIN_PAGE: MAIN_PAGE_TEMPLATE,
            GROUP_PAGE: GROUP_PAGE_TEMPLATE,
            AUTHOR_PAGE: AUTHOR_PAGE_TEMPLATE,
            PostsURLTests.POST_PAGE: POST_PAGE_TEMPLATE,
        }
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_anonymous_redirect_to_login(self):
        """Перенаправление анонимного пользователя на страницу логина."""
        url_names = {
            PostsURLTests.POST_EDIT_PAGE:
                PostsURLTests.POST_EDIT_REDIRECT,
            POST_CREATE_PAGE: POST_CREATE_REDIRECT,
            PostsURLTests.COMMENT_CREATE_PAGE:
                PostsURLTests.COMMENT_CREATE_REDIRECT,
        }
        for address, redirect in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect)

    def test_auth_user_redirect_to_post_page(self):
        """Перенаправление пользователя не являющегося автором
        на страницу записи.
        """
        response = self.auth_user_client.get(
            PostsURLTests.POST_EDIT_PAGE,
            follow=True
        )
        self.assertRedirects(response, PostsURLTests.POST_PAGE)

    def test_nonexistent_page_return_404(self):
        """Обращение к несуществующей странице возвращает ошибку 404."""
        response = self.guest_client.get(NONEXISTENT_PAGE)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, NONEXISTENT_PAGE_TEMPLATE)
