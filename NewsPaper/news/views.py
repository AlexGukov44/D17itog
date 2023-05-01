import pytz
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from requests import request
from datetime import datetime, timedelta

from django.http import HttpResponse
from django.views import View

from .models import Post, Category, BaseRegisterForm, Author, post, MyModel
from .forms import PostForm
from .filter import PostFilter
from django.contrib.auth.models import User, Group
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .tasks import send_email_task
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.translation import activate, get_supported_language_variant, LANGUAGE_SESSION_KEY



@login_required
def upgrade_me(request):
    Author.objects.create(user_author=request.user)
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(request.user)
    return redirect('/news/')


class PostList(LoginRequiredMixin, ListView):
    model = Post
    ordering = '-date_in'
    template_name = 'news.html'
    context_object_name = 'post_news'
    paginate_by = 50

    def get_context_data(self, **kwargs):  # забираем отфильтрованные объекты переопределяя метод get_context_data у наследуемого класса
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())  #вписываем фильтр в контекст
        context['categories'] = Category.objects.all()
        context['form'] = PostForm()
        context['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)  # создаём новую форму, забиваем в неё данные из POST-запроса

        if form.is_valid():  # если пользователь ввёл всё правильно и нигде не ошибся, то сохраняем новый пост
            form.save()

        return super().get(request, *args, **kwargs)


class PostDetail(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'onenews.html'
    context_object_name = 'onenews'
    queryset = Post.objects.all()

    def get_object(self, *args, **kwargs):  # переопределяем метод получения объекта
        obj = cache.get(f'post-{self.kwargs["pk"]}', None)
        # кэш очень похож на словарь, и метод get действует так же. Он забирает значение по ключу, если его нет, то забирает None.
        # если объекта нет в кэше, то получаем его и записываем в кэш
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)

        return obj


class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):   # создание поста
    permission_required = 'news.add_post'
    template_name = 'post_add.html'
    form_class = PostForm
    model = post

    def form_valid(self, form):
        post = form.save(commit=False)
        post.save()
        send_email_task.delay(post.pk)
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):   # редактирование поста
    permission_required = 'news.change_post'
    template_name = 'post_edit.html'
    form_class = PostForm

    # метод get_object мы используем вместо queryset, чтобы получить информацию об объекте редактирования
    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)


# дженерик для удаления поста
class PostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'news.delete_post'
    model = Post
    template_name = 'post_delete.html'
    queryset = Post.objects.all()
    success_url = '/news/'
    context_object_name = 'post_delete'


class PostSearch(ListView):   #поиск поста
    model = Post
    template_name = 'post_search.html'
    context_object_name = 'post_news'
    paginate_by = 50

    def get_queryset(self):  # получаем обычный запрос
        queryset = super().get_queryset()  # используем наш класс фильтрации
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/'


class CategoryListView(ListView):
    model = Post
    template_name = 'category_list.html'
    context_object_name = 'category_news_list'

    def get_queryset(self):
        self.category = get_object_or_404(Category, id=self.kwargs['pk'])
        queryset = Post.objects.filter(category=self.category).order_by('-date_in')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_subscriber'] = self.request.user not in self.category.subscribers.all()
        context['category'] = self.category
        return context


@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)
    message = 'вы подписались на категорию: '
    return render(request, 'subscribe.html', {'category': category, 'message': message})


@login_required
def unsubscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.remove(user)
    message = 'отписка от категории: '
    return render(request, 'subscribe.html', {'category': category, 'message': message})


class Index(View):
    def get(self, request):
        current_time = timezone.now()

        # .  Translators: This message appears on the home page only
        models = MyModel.objects.all()

        context = {
            'models': models,
            'current_time': timezone.now(),
            'timezones': pytz.common_timezones  # добавляем в контекст все доступные часовые пояса
        }

        return HttpResponse(render(request, 'default.html', context))

    #  по пост-запросу будем добавлять в сессию часовой пояс, который и будет обрабатываться написанным нами ранее middleware
    def post(self, request):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('/')

