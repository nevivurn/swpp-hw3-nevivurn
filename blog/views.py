from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import Article, Comment

def signup(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        req_data = json.loads(request.body.decode())
        username = req_data['username']
        password = req_data['password']
    except (KeyError, ValueError):
        return HttpResponse(status=400)
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
    except (KeyError, ValueError):
        return HttpResponse(status=400)
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

def articles(request):
    if request.method not in ['GET', 'POST']:
        return HttpResponseNotAllowed(['GET', 'POST'])

    if not request.user.is_authenticated:
        return HttpResponse(status=403)

    if request.method == 'GET':
        # article list
        article_list = [article for article in Article.objects.all().values()]
        # need to rename author_id to author
        for article in article_list:
            article['author'] = article['author_id']
            del article['author_id']
        return JsonResponse(article_list, safe=False)

    else: # request.method == 'POST':
        # new article
        try:
            req_data = json.loads(request.body)
            title = req_data['title']
            content = req_data['content']
            author_id = int(req_data['author'])
        except (KeyError, ValueError):
            return HttpResponse(status=400)
        if req_data.keys() - {'title', 'content', 'author'}:
            return HttpResponse(status=400)

        if author_id != request.user.pk:
            return HttpResponse(status=403)

        author = User.objects.get(pk=author_id)
        new_article = Article(title=title, content=content, author=author)
        new_article.save()

        response_dict = {
            'id': new_article.pk,
            'title': title,
            'content': content,
            'author': author_id,
        }

        return JsonResponse(response_dict, status=201)

@ensure_csrf_cookie
def token(request):
    if request.method == 'GET':
        return HttpResponse(status=204)
    else:
        return HttpResponseNotAllowed(['GET'])
