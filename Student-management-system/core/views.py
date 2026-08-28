from django.shortcuts import redirect, render


def home(request):
    return redirect('dashboard')


def about(request):
    return render(request, 'core/home.html')
