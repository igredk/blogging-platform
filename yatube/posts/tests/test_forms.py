"""Тестирование форм приложения posts."""
import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

AUTHOR = 'PostAuthor'
AUTHOR_PAGE = reverse(
    'posts:profile',
    kwargs={'username': AUTHOR}
)
POST_CREATE_PAGE = reverse('posts:post_create')

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание'
        )
        image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись',
            group=cls.group,
            image=image,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Тестовый комментарий',
        )
        cls.POST_PAGE = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_PAGE = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.COMMENT_CREATE_PAGE = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Автор записи
        self.author = PostCreateFormTests.author
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.image = SimpleUploadedFile(
            name='test_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовая запись для PostForm',
            'group': PostCreateFormTests.group.id,
            'image': self.image
        }
        response = self.author_client.post(
            POST_CREATE_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, AUTHOR_PAGE)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=PostCreateFormTests.group,
                image=f'posts/{self.image}'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Измененная запись',
            'group': '',
        }
        response = self.author_client.post(
            PostCreateFormTests.POST_EDIT_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PostCreateFormTests.POST_PAGE)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Измененная запись',
                group=None
            ).exists()
        )

    def test_comment_create(self):
        """Валидная форма создает комментарий в Comment."""
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Второй тестовый комментарий',
        }
        response = self.author_client.post(
            PostCreateFormTests.COMMENT_CREATE_PAGE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PostCreateFormTests.POST_PAGE)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post=PostCreateFormTests.post,
                text=form_data['text'],
            ).exists()
        )
