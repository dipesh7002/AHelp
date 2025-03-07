from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from helper.forms import UserSignupForm, AssignmentHelperForm

def login_user(request):
    if request.user.is_authenticated:
        return redirect("/user/home")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid:
            user = form.get_user() 
            login(request, user)
            return redirect('/user/home')
    else:
        form = AuthenticationForm()
    context = {"form": form}
    return render(request, "user/login.html", context)

class home(TemplateView):
    template_name = 'user/home.html'
    
def signup_view(request):
    if request.user.is_authenticated:
        redirect('helper page')
    if request.method == "POST":
        user_form = UserSignupForm(request.POST)
        helper_form = AssignmentHelperForm(request.POST, request.FILES) 
        if user_form.is_valid() and helper_form.is_valid():
            user = user_form.save()
            helper = helper_form.save(commit=False)
            helper.user = user
            helper.save()
            helper_form.save_m2m()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('helper page')
    else:
        user_form = UserSignupForm()
        helper_form = AssignmentHelperForm()
    return render(request, 'user middle', {'user_form' : user_form, 'helper_form': helper_form})


def logout_user(request):
    logout(request)
    return redirect('home:starting page')

class SignUp(TemplateView):
    template_name = 'user/middle.html'

class SignUpHelper(TemplateView):
    template_name = 'user/signup.html'

class HelperPage(TemplateView):
    template_name = 'user/helper.html'