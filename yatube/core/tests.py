from http import HTTPStatus
from django.test import TestCase


class ErrorURLTest(TestCase):
    def test_unexisting_page_404(self):
        """Несуществующая страница возвращает ошибку 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_use_correct_template(self):
        """Страница ошибки 404 использует соответствующий шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
