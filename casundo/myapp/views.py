from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Post
from django.urls import reverse_lazy




class HomePageView(TemplateView):
    template_name = 'myApp/home.html'

class AboutPageView(TemplateView):
    template_name = 'myApp/about.html'

class BlogListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'myApp/blog_list.html'

class BlogDetailView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'myApp/blog_detail.html'

class BlogCreateView(CreateView):
    model = Post
    fields = ['title', 'author', 'body']
    template_name = 'myApp/blog_create.html'

class BlogUpdateView(UpdateView):
    model = Post
    fields = ['title', 'author', 'body']
    template_name = 'myApp/blog_update.html'

class BlogDeleteView(DeleteView):
    model = Post
    template_name = 'myApp/blog_delete.html'
    success_url = reverse_lazy('blog')