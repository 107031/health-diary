from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse


@login_required
def observations(request):
    return redirect(reverse('statistics') + '?period=month#observations')
