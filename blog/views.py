from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden, JsonResponse
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
        return HttpResponseBadRequest()
    if req_data.keys() - {'username', 'password'}:
        return HttpResponseBadRequest()

    try:
        User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return HttpResponseBadRequest()

    return HttpResponse(status=201)

def signin(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        req_data = json.loads(request.body.decode())
        username = req_data['username']
        password = req_data['password']
    except (KeyError, ValueError):
        return HttpResponseBadRequest()
    if req_data.keys() - {'username', 'password'}:
        return HttpResponseBadRequest()

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
        return HttpResponseForbidden()

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
        except (KeyError, ValueError):
            return HttpResponseBadRequest()
        if req_data.keys() - {'title', 'content'}:
            return HttpResponseBadRequest()

        new_article = Article(title=title, content=content, author=request.user)
        new_article.save()

        response_dict = {
            'id': new_article.id,
            'title': title,
            'content': content,
            'author': request.user.id,
        }

        return JsonResponse(response_dict, status=201)

def article(request, aid):
    if request.method not in ['GET', 'PUT', 'DELETE']:
        return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE'])

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    try:
        article = Article.objects.get(id=aid)
    except Article.DoesNotExist:
        return HttpResponseNotFound()

    if request.method == 'GET':
        # view article
        response_dict = {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'author': article.author_id,
        }
        return JsonResponse(response_dict)

    elif request.method == 'PUT':
        # edit article
        if request.user != article.author:
            return HttpResponseForbidden()

        try:
            req_data = json.loads(request.body)
            title = req_data['title']
            content = req_data['content']
        except KeyError:
            return HttpResponseBadRequest()
        if req_data.keys() - {'title', 'content'}:
            return HttpResponseBadRequest()

        article.title = title
        article.content = content
        article.save()

        response_dict = {
            'id': article.id,
            'title': title,
            'content': content,
            'author': article.author_id,
        }
        return JsonResponse(response_dict)

    else: # request.method == 'DELETE':
        # delete article
        if request.user != article.author:
            return HttpResponseForbidden()

        article.delete()
        return HttpResponse(status=200)

@ensure_csrf_cookie
def token(request):
    if request.method == 'GET':
        return HttpResponse(status=204)
    else:
        return HttpResponseNotAllowed(['GET'])
