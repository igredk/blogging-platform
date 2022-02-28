"""Тестирование путей приложения about."""
from http import HTTPStatus

from django.test import TestCase, Client

AUTHOR_PAGE = '/about/author/'
AUTHOR_PAGE_TEMPLATE = 'about/author.html'

TECH_PAGE = '/about/tech/'
TECH_PAGE_TEMPLATE = 'about/tech.html'


class AboutURLTests(TestCase):
    def setUp(self):
        # Неавторизованный пользователь
        self.guest_client = Client()

    def test_urls_templates(self):
        """Страницы доступны всем пользователям и
        используют соответствующий HTML-шаблон."""
        url_names = {
            AUTHOR_PAGE: AUTHOR_PAGE_TEMPLATE,
            TECH_PAGE: TECH_PAGE_TEMPLATE,
        }
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
