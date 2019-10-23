from django.http import HttpResponse, HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from json.decoder import JSONDecodeError

def signup(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        req_data = json.loads(request.body.decode())
        username = req_data['username']
        password = req_data['password']
    except (KeyError, JSONDecodeError):
        return HttpResponse(status=400)
    # extra keys
    if req_data.keys() - {'username', 'password'}:
        return HttpResponse(status=400)

    try:
        User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return HttpResponse(status=400)

    return HttpResponse(status=201)

def signin(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        req_data = json.loads(request.body.decode())
        username = req_data['username']
        password = req_data['password']
    except (KeyError, JSONDecodeError):
        return HttpResponse(status=400)
    # extra keys
    if req_data.keys() - {'username', 'password'}:
        return HttpResponse(status=400)

    user = authenticate(request, username=username, password=password)
    if user == None:
        return HttpResponse(status=401)

    login(request, user)
    return HttpResponse(status=204)

def signout(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    logout(request)
    return HttpResponse(status=204)

@ensure_csrf_cookie
def token(request):
    if request.method == 'GET':
        return HttpResponse(status=204)
    else:
        return HttpResponseNotAllowed(['GET'])
