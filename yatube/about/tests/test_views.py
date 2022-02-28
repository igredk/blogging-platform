"""Тестирование view-функций приложения about."""
from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

AUTHOR_PAGE = reverse('about:author')
AUTHOR_PAGE_TEMPLATE = 'about/author.html'

TECH_PAGE = reverse('about:tech')
TECH_PAGE_TEMPLATE = 'about/tech.html'


class AboutURLTests(TestCase):
    def setUp(self):
        # Неавторизованный пользователь
        self.guest_client = Client()

    def test_url_names(self):
        """При обращении к name страница доступна и
        вызывается соответствующий HTML-шаблон."""
        templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
