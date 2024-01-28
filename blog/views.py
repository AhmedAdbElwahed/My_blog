from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.db.models import Count

from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm


# Create your views here.
# function based view
def post_list(request, tag_slug=None):
    posts_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags__slug__in=[tag])
    paginator = Paginator(posts_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    context = {'posts': posts, 'tag': tag}
    return render(request, 'blog/post/list.html', context)


# class CustomPaginator(Paginator):
#     def validate_number(self, number: int | float | str | None) -> int:
#         try:
#             return super().validate_number(number)
#         except PageNotAnInteger:
#             return 1
#         except EmptyPage:
#             if int(number) > 1:
#                 return self.num_pages
#             elif int(number) < 1:
#                 return 1
#             else:
#                 raise

# class PostListView(ListView):
#     """
#     Alternative post list view
#     """
#     # queryset = Post.published.all()
#     # context_object_name = 'posts'
#     model = Post
#     paginate_by = 3
#     paginator_class = CustomPaginator
#     template_name = 'blog/post/list.html'

#     def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
#         context =  super(PostListView, self).get_context_data(**kwargs)
#         post_list = Post.published.all()
#         paginator = self.paginator_class(post_list, self.paginate_by)
#         page_number = self.request.GET.get('page', 1)
#         try:
#             posts = paginator.page(page_number)
#         except PageNotAnInteger:
#             posts = paginator.page(1)
#         context['posts'] = posts
#         return context


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             status=Post.Status.PUBLISHED)
    comments = post.comments.filter(active=True)
    form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    return render(request, 'blog/post/detail.html', {'post': post,
                                                     'comments': comments,
                                                     'form': form,
                                                     'similar_posts': similar_posts,})


def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    error = None
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            try:
                send_mail(subject, message, 'the smtp host name', [cd['to']])
                sent = True
            except Exception:
                error = f'An Error Occurred During sending the email, try later'
    else:
        form = EmailPostForm()

    context = {'post': post, 'form': form, 'sent': sent, 'error': error}
    return render(request, 'blog/post/share.html', context)


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post': post,
                   'form': form,
                   'comment': comment})

# send_mail('hello', 'hello from django', 'ahmedabdelwhed68@gmail.com', ['mostafaabdelwahed960@gmail.com'])
