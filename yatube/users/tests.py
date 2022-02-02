from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()


class UsersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Username')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_not_auth(self):
        """
        Проверка доступности адресов страниц
        для неавторизованного пользователя.
        """
        urls_not_auth = (
            '/auth/login/',
            '/auth/signup/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/done/'
        )
        for url in urls_not_auth:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_auth(self):
        """
        Проверка доступности адресов страниц
        для авторизованного пользователя.
        """
        urls_auth = (
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/logout/',
        )
        for url in urls_auth:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anon_users_pages_uses_correct_template(self):
        """
        URL-адреса users используют соответствующий шаблон.
        Для анонимного пользователя.
        """
        templates_pages_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse(
                'users:password_reset_form'
            ): 'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'
            ): 'users/password_reset_done.html',
            reverse(
                'users:password_reset_complete'
            ): 'users/password_reset_complete.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_auth_users_pages_uses_correct_template(self):
        """
        URL-адреса users используют соответствующий шаблон.
        Для авторизованного пользователя.
        """
        templates_pages_names = {
            reverse(
                'users:password_change'
            ): 'users/password_change_form.html',
            reverse(
                'users:password_change_done'
            ): 'users/password_change_done.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_users_signup_form(self):
        """Проверка формы регистрации пользователя."""
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_new_user(self):
        """Регистрация нового пользователя."""
        posts_count = User.objects.count()
        form_data = {
            'first_name': 'FirstName',
            'last_name': 'LastName',
            'username': 'NewUser',
            'email': 'drunya_11995@mail.ru',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('users:login'))
        self.assertEqual(User.objects.count(), posts_count + 1)
