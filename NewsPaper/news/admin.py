from django.contrib import admin
from .models import Post, Category, MyModel
from modeltranslation.admin import TranslationAdmin


class PostAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Post._meta.get_fields()] # генерируем список имен полей
    list_display = ('title', 'category')


class CategoryAdmin(TranslationAdmin):
    model = Category


class MyModelAdmin(TranslationAdmin):
    model = MyModel


admin.site.register(MyModel)
admin.site.register(Post)
admin.site.register(Category)
