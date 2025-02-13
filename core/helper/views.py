from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class HelperHome(LoginRequiredMixin, TemplateView):
    template_name = "helper/index.html"

