from django.urls import path
from .views import PostList, PostDetail, PostUpdateView, PostDeleteView, PostCreateView, PostSearch, BaseRegisterView
from django.contrib.auth.views import LoginView, LogoutView
from .views import upgrade_me, CategoryListView, subscribe, unsubscribe

urlpatterns = [
    path('', PostList.as_view()),
    path('<int:pk>', PostDetail.as_view(), name='post_detail'),
    path('create/', PostCreateView.as_view(), name='post_add'),
    path('edit/<int:pk>', PostUpdateView.as_view(), name='post_edit'),
    path('delete/<int:pk>', PostDeleteView.as_view(), name='post_delete'),
    path('search/', PostSearch.as_view(), name='post_search'),
    path('login/',
         LoginView.as_view(template_name='news/login.html'),
         name='login'),
    path('logout/',
         LogoutView.as_view(template_name='news/logout.html'),
         name='logout'),
    path('signup/',
         BaseRegisterView.as_view(template_name='news/signup.html'),
         name='signup'),
    path('upgrade/', upgrade_me, name='upgrade'),
    path('categories/<int:pk>', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/subscribe', subscribe, name='subscribe'),
    path('categories/<int:pk>/unsubscribe', unsubscribe, name='unsubscribe'),
]
 