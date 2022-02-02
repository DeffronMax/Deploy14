from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings

from .forms import PostForm, CommentForm, GroupForm
from .models import Group, Post, User, Comment, Follow, Like, LikeComment


# @cache_page(10)
def index(request):
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    post_list = Post.objects.select_related('author', 'group').all()
    if request.user.is_authenticated:
        follow_count = Follow.objects.select_related('author').filter(
            user=request.user
        ).count()
    else:
        follow_count = 0
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
        'follow_count': follow_count,
        'DEBUG': settings.DEBUG,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    posts_count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=author,
            user=request.user
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following
    }
    return render(request, template, context)


def post_view(request, post_id):
    template = 'posts/post_detail.html'
    post = Post.objects.select_related('author', 'group').get(pk=post_id)
    posts_count = post.author.posts.all().count()
    like_count = Like.objects.filter(post=post_id).count()
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(
            user=request.user,
            post=post_id
        ).exists()
    else:
        is_liked = False
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    comment_count = Comment.objects.filter(post=post_id).count()
    context = {
        'post': post,
        'posts_count': posts_count,
        'like_count': like_count,
        'comment_count': comment_count,
        'is_liked': is_liked,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required()
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        form_post = form.save(commit=False)
        form_post.author = request.user
        form_post.save()
        return redirect('posts:profile', username=request.user)
    context = {
        'form': form,
        'is_create': True
    }
    return render(request, template, context)


@login_required()
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user == post.author:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if request.method == 'POST' and form.is_valid():
            form_post = form.save(commit=False)
            form_post.author = request.user
            form_post.save()
            return redirect('posts:post_detail', post_id=post_id)
        context = {
            'form': form,
        }
        return render(request, template, context)
    return redirect('posts:post_detail', post_id=post_id)


@login_required()
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        post.delete()
        return redirect('posts:profile', username=request.user)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        post.comments_count += 1
        post.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def delete_comment(request, post_id, com_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=com_id)
    if comment.author == request.user or post.author == request.user:
        comment.delete()
        post.comments_count -= 1
        post.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def like_comment(request, post_id, com_id):
    comment = Comment.objects.select_related('author', 'post').get(id=com_id)
    like = LikeComment.objects.filter(
        user=request.user,
        comment=com_id
    ).exists()
    if not like:
        LikeComment.objects.create(
            user=request.user,
            comment=comment
        )
        comment.like += 1
        comment.save()
    else:
        LikeComment.objects.filter(
            user__username=request.user,
            comment=com_id
        ).delete()
        comment.like -= 1
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.select_related('author', 'group').filter(
        author__following__user=request.user
    )
    follow_count = Follow.objects.select_related('author').filter(
        user=request.user
    ).count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'follow_count': follow_count,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=request.user,
        author=author).exists()
    if request.user != author and not follow:
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        author__username=username,
        user__username=request.user
    ).delete()
    return redirect('posts:profile', username=username)


@login_required
def like_index(request):
    template = 'posts/likes.html'
    follow_count = Follow.objects.select_related('author').filter(
        user=request.user
    ).count()
    post_list = Post.objects.select_related('author', 'group').filter(
        liked__user=request.user
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'follow_count': follow_count,
    }
    return render(request, template, context)


@login_required
def post_like(request, post_id):
    post = Post.objects.select_related('author', 'group').get(pk=post_id)
    like = Like.objects.filter(
        user=request.user,
        post=post_id
    ).exists()
    if not like:
        Like.objects.create(
            user=request.user,
            post=post
        )
        post.likes_count += 1
        post.save()
    else:
        Like.objects.filter(
            user__username=request.user,
            post=post_id
        ).delete()
        post.likes_count -= 1
        post.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def group_create(request):
    template = 'posts/create_group.html'
    form = GroupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:index')
    context = {
        'form': form
    }
    return render(request, template, context)
