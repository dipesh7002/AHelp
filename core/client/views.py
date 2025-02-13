from django.shortcuts import render, redirect
from django.views.generic import UpdateView, ListView,CreateView, DeleteView, TemplateView,DetailView
from django.urls import reverse_lazy
from .models import PostAssignment
from client.forms import PostForm
from django.contrib.auth.mixins import LoginRequiredMixin 

class ClientHome(LoginRequiredMixin, TemplateView):
    template_name = "client/index.html"


class AssignmentCreate(CreateView):
    form_class = PostForm
    template_name = 'client/create.html'
    success_url = reverse_lazy('client:client-home')

class AssignmentView(ListView):
    model = PostAssignment
    context_object_name ='assignments'
    template_name = 'client/view.html'

class AssignmentDetail(DetailView):
    model = PostAssignment
    context_object_name= 'assignment'
    template_name = 'client/detail.html'
