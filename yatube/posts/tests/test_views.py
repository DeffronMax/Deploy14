import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from ..models import Group, Post, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(
            username='Username',
            first_name='User',
        )
        cls.group1 = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовое название 2',
            slug='test-slug-2',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group1,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_posts_pages_uses_correct_template(self):
        """URL-адреса posts используют соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'Username'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        index_object = response.context['page_obj'][0]
        post_author_0 = index_object.author
        post_text_0 = index_object.text
        post_group_0 = index_object.group
        post_image_0 = index_object.image
        self.assertEqual(str(post_author_0), 'Username')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(str(post_group_0), 'Тестовое название')
        self.assertEqual(str(post_image_0), 'posts/small.gif')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        group_list_object = response.context['page_obj'][0]
        post_author_0 = group_list_object.author
        post_text_0 = group_list_object.text
        post_group_0 = group_list_object.group
        post_image_0 = group_list_object.image
        self.assertEqual(str(post_author_0), 'Username')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(str(post_group_0), 'Тестовое название')
        self.assertEqual(response.context['group'].title, 'Тестовое название')
        self.assertEqual(response.context['group'].slug, 'test-slug')
        self.assertEqual(
            response.context['group'].description, 'Тестовое описание'
        )
        self.assertEqual(str(post_image_0), 'posts/small.gif')

    def test_no_post_in_another_group(self):
        """Проверяем, что пост не попал в чужую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'})
        )
        list_object = response.context.get('page_obj').object_list
        self.assertEqual(len(list_object), 0)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Username'})
        )
        profile_object = response.context['page_obj'][0]
        post_author_0 = profile_object.author
        post_text_0 = profile_object.text
        post_group_0 = profile_object.group
        post_image_0 = profile_object.image
        self.assertEqual(str(post_author_0), 'Username')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(str(post_group_0), 'Тестовое название')
        self.assertEqual(str(post_image_0), 'posts/small.gif')
        self.assertEqual(response.context['author'].username, 'Username')
        self.assertEqual(response.context['author'].first_name, 'User')
        self.assertEqual(response.context['posts_count'], 1)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(str(response.context['post'].author), 'Username')
        self.assertEqual(response.context['post'].text, 'Тестовый текст')
        self.assertEqual(
            str(response.context['post'].group), 'Тестовое название'
        )
        self.assertEqual(
            str(response.context['post'].image), 'posts/small.gif'
        )
        self.assertEqual(response.context['posts_count'], 1)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    """Тест паджинатора."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Username')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group
            )

    def setUp(self):
        self.urls = {
            'posts:index': '',
            'posts:group_list': {'slug': 'test-slug'},
            'posts:profile': {'username': 'Username'}
        }
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10."""
        for url, kwarg in self.urls.items():
            with self.subTest(url=url):
                response = self.client.get(reverse(url, kwargs=kwarg))
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверяем, что на второй странице три поста."""
        for url, kwarg in self.urls.items():
            with self.subTest(url=url):
                response = self.client.get(
                    reverse(url, kwargs=kwarg) + '?page=2'
                )
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_second_page_show_correct_context(self):
        """Содержимое постов на второй странице соответствует ожиданиям."""
        for url, kwarg in self.urls.items():
            with self.subTest(url=url):
                response = self.client.get(
                    reverse(url, kwargs=kwarg) + '?page=2'
                )
                second_object = response.context.get(
                    'page_obj'
                ).object_list[1]
                post_author_1 = second_object.author
                post_text_1 = second_object.text
                post_group_1 = second_object.group
                self.assertEqual(str(post_author_1), 'Username')
                self.assertEqual(post_text_1, 'Тестовый текст')
                self.assertEqual(str(post_group_1), 'Тестовое название')


class CommentsViewsTest(TestCase):
    """Тест комментариев."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Username')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_detail_contains_comment(self):
        """Комментарий появляется на странице поста."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(
            str(response.context['comments'][0].author), 'Username'
        )
        self.assertEqual(
            response.context['comments'][0].text, 'Тестовый комментарий'
        )

    def test_auth_add_comment(self):
        """Авторизованный пользователь добавляет комментарий."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.authorized_client,
            'text': 'Тестовый комментарий 2',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_anon_add_comment(self):
        """Запрет на добавление комментария анонимному пользователю."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'Тестовый комментарий 2',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)


class CacheTest(TestCase):
    """Тест кэша."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Username')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_cache_index_page(self):
        """Проверяем работу кэша на главной странице."""
        posts_count = Post.objects.count()
        response = self.guest_client.get(reverse('posts:index'))
        context = response.context['page_obj']
        self.assertEqual(context[0], self.post)
        self.post.delete()
        self.assertEqual(Post.objects.count(), posts_count - 1)
        response = self.guest_client.get(reverse('posts:index'))
        old_content = response.content.decode('UTF-8')
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        new_content = response.content.decode('UTF-8')
        self.assertNotEqual(old_content, new_content)
        self.assertIn('Тестовый текст', old_content)
        self.assertNotIn('Тестовый текст', new_content)


class FollowTest(TestCase):
    """Тест подписок."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='Username')
        cls.user2 = User.objects.create_user(username='User')
        cls.author = User.objects.create_user(username='User_author')
        cls.post1 = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.follow = Follow.objects.create(
            user=cls.user2,
            author=cls.author
        )

    def setUp(self):
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        cache.clear()

    def test_auth_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        follow_count = Follow.objects.count()
        response = self.authorized_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'User_author'}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'User_author'})
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(
            Follow.objects.get(id=2).author, self.author
        )
        self.assertEqual(
            Follow.objects.get(id=2).user, self.user1
        )

    def test_auth_unfollow(self):
        """Авторизованный пользователь может отписаться от автора."""
        follow_count = Follow.objects.count()
        response = self.authorized_client2.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': 'User_author'}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'User_author'})
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_followers(self):
        """Новый пост автора появляется в ленте у подписчиков."""
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        old_context = response.context['page_obj']
        self.assertEqual(len(old_context), 1)
        self.assertEqual(old_context[0], self.post1)
        post2 = Post.objects.create(
            author=self.author,
            text='Тестовый текст 2',
        )
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        new_context = response.context['page_obj']
        self.assertEqual(len(new_context), 2)
        self.assertEqual(new_context[0], post2)

    def test_no_new_post_unfollowers(self):
        """Новый пост не появляется у тех, кто не подписан."""
        response = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        old_context = response.context['page_obj']
        self.assertEqual(len(old_context), 0)
        Post.objects.create(
            author=self.author,
            text='Тестовый текст 2',
        )
        response = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        new_context = response.context['page_obj']
        self.assertEqual(len(new_context), 0)

    def test_follow_on_one_author_many_times(self):
        """Проверяем запрет на подписку на одного автора несколько раз."""
        follow_count = Follow.objects.count()
        response = self.authorized_client2.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'User_author'}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'User_author'})
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_yourself(self):
        """Проверяем запрет на подписку на самого себя."""
        follow_count = Follow.objects.count()
        response = self.authorized_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'Username'}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'Username'})
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_following_button(self):
        """Проверка кнопки Подписаться/Отписаться."""
        response = self.authorized_client2.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'User_author'}
            )
        )
        context = response.context['following']
        self.assertTrue(context)
        response = self.authorized_client1.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'User_author'}
            )
        )
        context = response.context['following']
        self.assertFalse(context)
