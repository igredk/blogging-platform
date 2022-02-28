"""Application for working with user posts."""
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.shortcuts import (redirect,
                              render,
                              get_object_or_404,
                              get_list_or_404
                              )

from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm

CACHE_LMT = 20
POST_LMT = 10


def paginator_page(request, post_list):
    paginator = Paginator(post_list, POST_LMT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(CACHE_LMT, key_prefix='index_page')
def index(request):
    """View-func for '' request.

    Displays ten posts per page, sorted by date added.
    Returns 'posts/index.html' template.
    """
    post_list = Post.objects.all()
    page_obj = paginator_page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    cache.clear()
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """View-func for 'group/<slug:slug>/' request.

    Displays ten posts per page, sorted by group and date added.
    Returns 'posts/group_list.html' template.
    """
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group.all()
    page_obj = paginator_page(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """View-func for 'profile/<str:username>/' request.

    Displays ten posts per page, sorted by author and date added.
    Returns 'posts/profile.html' template.
    """
    user = request.user
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    page_obj = paginator_page(request, author_posts)

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=user, author=author).exists()
    else:
        following = False

    context = {
        'author': author,
        'author_posts': author_posts,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """View-func for 'posts/<int:post_id>/' request.

    Shows detailed information about a post.
    Returns 'posts/post_detail.html' template.
    """
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, username=post.author.username)
    author_posts = get_list_or_404(Post, author=author)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    is_author = request.user == post.author
    context = {
        'post': post,
        'author_posts': author_posts,
        'form': form,
        'comments': comments,
        'is_author': is_author,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """View-func for 'create/' request.

    Creates a post from PostForm. If the form is valid,
    redirects to the author's page.
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """View-func for 'posts/<int:post_id>/edit/' request.

    Edit a post if the requester is the author. If the form is valid,
    redirects to the post page.
    """
    post = get_object_or_404(Post, id=post_id)
    # Editing is allowed if the requester is the author
    if request.user == post.author:
        if request.method == 'POST':
            form = PostForm(
                request.POST,
                files=request.FILES or None,
                instance=post
            )
            if form.is_valid:
                post = form.save(commit=False)
                post.author = request.user
                post.save()
                return redirect('posts:post_detail', post_id=post.pk)
        else:
            form = PostForm(instance=post)
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': True}
        )
    return redirect('posts:post_detail', post_id=post.pk)


@login_required
def add_comment(request, post_id):
    """View-func for 'posts/<int:post_id>/comment/' request.

    Adds a comment to a post and redirects to the post page.
    """
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    follow_list = Follow.objects.filter(user=user)
    author_list = [follower.author for follower in follow_list]
    post_list = Post.objects.filter(author__in=author_list)
    page_obj = paginator_page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.create(user=user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:index')
