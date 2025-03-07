from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from .forms import SignupForm

def login_user(request):
    form = AuthenticationForm()
    if request.user.is_authenticated:
        return redirect("/user/home")
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/user/home')

    context = {"form": form}
    return render(request, "user/login.html", context)

class home(TemplateView):
    template_name = 'user/home.html'
    
def signup_view(request):
    form = SignupForm(request.POST)
    if form.is_valid():
        user = form.save()
        user.refresh_from_db()
        user.profile.first_name = form.cleaned_data.get('first_name')
        user.profile.last_name = form.cleaned_data.get('last_name')
        user.profile.email = form.cleaned_data.get('email')
        user.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('/user/login')
    else:
        form = SignupForm()
    return render(request, 'user/signup.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('home:starting page')

class signUpMiddle(TemplateView):
    template_name = 'user/sign_up_middle.html'