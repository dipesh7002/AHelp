from django.shortcuts import render, redirect
from django.views.generic import TemplateView

class startingPage(TemplateView):

    template_name = 'home/index.html'
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('client/home')
        return super().get(request, *args, **kwargs)

class AboutUsPage(TemplateView):
    template_name = 'home/about_us.html'
    