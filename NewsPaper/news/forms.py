from django.forms import ModelForm, BooleanField
from .models import Post
from allauth.account.forms import SignupForm
from django.contrib.auth.models import Group


class PostForm(ModelForm):
    check_box = BooleanField(label='подтвердить')  # добавляем галочку, или же true-false поле

    class Meta:
        model = Post
        fields = ['title', 'text', 'category', 'author_post', 'post_news', 'check_box']
        # не забываем включить галочку в поля, иначе она не будет показываться на странице!


class BasicSignupForm(SignupForm):

    def save(self, request):
        user = super(BasicSignupForm, self).save(request)
        basic_group = Group.objects.get(name='common')
        basic_group.user_set.add(user)
        return user
