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

    req_data = json.loads(request.body.decode())
    username = req_data['username']
    password = req_data['password']

    try:
        User.objects.create_user(username=username, password=password)
    except IntegrityError:
        # duplicate user
        return HttpResponseBadRequest()

    return HttpResponse(status=201)

def signin(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    req_data = json.loads(request.body.decode())
    username = req_data['username']
    password = req_data['password']

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
        article_list = list(Article.objects.all().values())
        # need to rename author_id to author
        for article in article_list:
            article['author'] = article['author_id']
            del article['author_id']
        return JsonResponse(article_list, safe=False)

    else: # request.method == 'POST':
        # new article
        req_data = json.loads(request.body)
        title = req_data['title']
        content = req_data['content']

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

        req_data = json.loads(request.body)
        title = req_data['title']
        content = req_data['content']

        article.title = title
        article.content = content
        article.save()

        response_dict = {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'author': article.author_id,
        }
        return JsonResponse(response_dict)

    else: # request.method == 'DELETE':
        # delete article
        if request.user != article.author:
            return HttpResponseForbidden()

        article.delete()
        return HttpResponse(status=200)

def article_comment(request, aid):
    if request.method not in ['GET', 'POST']:
        return HttpResponseNotAllowed(['GET', 'POST'])

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    try:
        article = Article.objects.get(id=aid)
    except Article.DoesNotExist:
        return HttpResponseNotFound()

    if request.method == 'GET':
        comment_list = list(Comment.objects.filter(article=article).order_by('id').values())
        # rename _id fields to just themselves
        for comment in comment_list:
            comment['article'] = comment['article_id']
            del comment['article_id']
            comment['author'] = comment['author_id']
            del comment['author_id']
        return JsonResponse(comment_list, safe=False)

    else: # request.method == 'POST':
        # new comment
        req_data = json.loads(request.body)
        content = req_data['content']

        new_comment = Comment(article=article, content=content, author=request.user)
        new_comment.save()

        response_dict = {
            'id': new_comment.id,
            'article': new_comment.article_id,
            'content': new_comment.content,
            'author': new_comment.author_id,
        }
        return JsonResponse(response_dict, status=201)

def comments(request, cid):
    if request.method not in ['GET', 'PUT', 'DELETE']:
        return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE'])

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    try:
        comment = Comment.objects.get(id=cid)
    except Comment.DoesNotExist:
        return HttpResponseNotFound()

    if request.method == 'GET':
        # view article
        response_dict = {
            'id': comment.id,
            'article': comment.article_id,
            'content': comment.content,
            'author': comment.author_id,
        }
        return JsonResponse(response_dict)

    elif request.method == 'PUT':
        # edit comment
        if request.user != comment.author:
            return HttpResponseForbidden()

        req_data = json.loads(request.body)
        content = req_data['content']

        comment.content = content
        comment.save()

        response_dict = {
            'id': comment.id,
            'article': comment.article_id,
            'content': comment.content,
            'author': comment.author_id,
        }
        return JsonResponse(response_dict)

    else: # request.method == 'DELETE':
        # delete comment
        if request.user != comment.author:
            return HttpResponseForbidden()

        comment.delete()
        return HttpResponse(status=200)

@ensure_csrf_cookie
def token(request):
    if request.method == 'GET':
        return HttpResponse(status=204)
    else:
        return HttpResponseNotAllowed(['GET'])
