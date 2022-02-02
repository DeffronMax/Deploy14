from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='Username')
        cls.user2 = User.objects.create_user(username='Name')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post1 = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст',
            group=cls.group
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)

    def test_pages_for_anon(self):
        """Страницы, доступные любому пользователю."""
        urls_for_anon = {
            'posts:index': '',
            'posts:group_list': {'slug': 'test-slug'},
            'posts:profile': {'username': 'Username'},
            'posts:post_detail': {'post_id': '1'},
        }
        for url, kwarg in urls_for_anon.items():
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url, kwargs=kwarg))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_edit(self):
        """Страницы, доступные авторизованному пользователю."""
        urls_for_auth = {
            'posts:post_create': '',
            'posts:post_edit': {'post_id': '1'},
        }
        for url, kwarg in urls_for_auth.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwarg)
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_anon(self):
        """Запрет на создание поста анонимному пользователю."""
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_not_author_edit_delete(self):
        """Запрет на редактирование и удаление чужого поста."""
        urls = {
            'posts:post_edit': {'post_id': '2'},
            'posts:post_delete': {'post_id': '2'},
        }
        for url, kwarg in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwarg)
                )
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(
                    response,
                    reverse('posts:post_detail', kwargs={'post_id': '2'})
                )

    def test_create_redirect_anonymous(self):
        """
        Страница /create/ перенаправляет анонимного пользователя
        на страницу авторизации.
        """
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True
        )
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next={reverse("posts:post_create")}'
        )

    def test_edit_redirect(self):
        """Переадресация при успешном редактировании поста."""
        form_data = {'text': 'Измененный текст'}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post1.id}),
            data=form_data)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )

    def test_delete_redirect(self):
        """Переадресация при успешном удалении поста."""
        response = self.authorized_client.get(
            reverse('posts:post_delete', kwargs={'post_id': '1'}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'Username'})
        )
