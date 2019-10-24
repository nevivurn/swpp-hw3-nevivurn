from django.test import TestCase, Client
from django.contrib.auth import get_user
import json

class BlogTestCase(TestCase):
    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)

        # not get
        response = client.options('/api/token/')
        self.assertEqual(response.status_code, 405)

        # no csrf
        response = client.post('/api/signup/', {'username': 'chris', 'password': 'chris'},
                content_type='application/json')
        self.assertEqual(response.status_code, 403)

        # add csrf
        response = client.get('/api/token/')
        self.assertEqual(response.status_code, 204)
        csrftoken = response.cookies['csrftoken'].value

        # re-request
        response = client.post('/api/signup/', {'username': 'chris', 'password': 'chris'},
                content_type='application/json', HTTP_X_CSRFTOKEN=csrftoken)
        self.assertEqual(response.status_code, 201)

    def test_signup(self):
        client = Client()

        # not post
        response = client.get('/api/signup/')
        self.assertEqual(response.status_code, 405)

        # normal signup
        resposne = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(resposne.status_code, 201)

        # duplicate user
        resposne = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(resposne.status_code, 400)

    def test_signin(self):
        client = Client()

        # not post
        response = client.options('/api/signin/')
        self.assertEqual(response.status_code, 405)

        # test user
        response = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # incorrect
        response = client.post('/api/signin/', {'username': 'user', 'password': 'incorrect'},
                content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(get_user(client).is_authenticated)

        # correct password
        response = client.post('/api/signin/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)

    def test_signout(self):
        client = Client()

        # not get
        response = client.options('/api/signout/')
        self.assertEqual(response.status_code, 405)

        # create test user
        response = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # log in
        response = client.post('/api/signin/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # regular signout
        self.assertTrue(get_user(client).is_authenticated)
        response = client.get('/api/signout/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(get_user(client).is_authenticated)

        # signout while signed out is an error
        response = client.get('/api/signout/')
        self.assertEqual(response.status_code, 401)

    def test_articles(self):
        client = Client()

        # not get, post
        response = client.options('/api/article/')
        self.assertEqual(response.status_code, 405)

        # not signed in
        response = client.get('/api/article/')
        self.assertEqual(response.status_code, 403)

        # test user
        response = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # log in
        response = client.post('/api/signin/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # create
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        new_article = response.json()
        self.assertEqual(new_article['title'], 'title')
        self.assertEqual(new_article['content'], 'content')
        self.assertEqual(new_article['author'], get_user(client).id)

        # retrieve article
        response = client.get('/api/article/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0], new_article)

    def test_article_get(self):
        client = Client()

        # not get, put, delete
        response = client.options('/api/article/1/')
        self.assertEqual(response.status_code, 405)

        # not signed in
        response = client.get('/api/article/1/')
        self.assertEqual(response.status_code, 403)

        # test user
        response = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # log in
        response = client.post('/api/signin/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # nonexistent
        response = client.get('/api/article/1/')
        self.assertEqual(response.status_code, 404)

        # test article
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        article = response.json()

        # retrieve article
        response = client.get(f'/api/article/{article["id"]}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), article)

    def test_article_put_delete(self):
        client = Client()

        # create test user1
        response = client.post('/api/signup/', {'username': 'user1', 'password': 'pass'},
                content_type='application/json')

        # log in user1
        response = client.post('/api/signin/', {'username': 'user1', 'password': 'pass'},
                content_type='application/json')
        user1 = get_user(client)

        # create test article1
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        article1 = response.json()

        client.get('/api/signout/')

        # create test user2
        response = client.post('/api/signup/', {'username': 'user2', 'password': 'pass'},
                content_type='application/json')

        # log in user2
        response = client.post('/api/signin/', {'username': 'user2', 'password': 'pass'},
                content_type='application/json')
        user2 = get_user(client)

        # create test article2
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        article2 = response.json()

        # not same user
        response = client.put(f'/api/article/{article1["id"]}/', {})
        self.assertEqual(response.status_code, 403)

        # correct put
        response = client.put(f'/api/article/{article2["id"]}/', {'title': 'title2', 'content': 'content2'},
                content_type='application/json')
        self.assertEqual(response.status_code, 200)

        article2['title'] = 'title2'
        article2['content'] = 'content2'

        response = client.get(f'/api/article/{article2["id"]}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), article2)

        response = client.delete(f'/api/article/{article1["id"]}/')
        self.assertEqual(response.status_code, 403)

        response = client.delete(f'/api/article/{article2["id"]}/')
        self.assertEqual(response.status_code, 200)

        # check if deleted
        response = client.get('/api/article/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0], article1)

    def test_article_comment_get(self):
        client = Client()

        # not get,post
        response = client.options('/api/article/1/comment/')
        self.assertEqual(response.status_code, 405)

        # not signed in
        response = client.get('/api/article/1/comment/')
        self.assertEqual(response.status_code, 403)

        # test user
        response = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # log in
        response = client.post('/api/signin/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # nonexistent
        response = client.get('/api/article/1/comment/')
        self.assertEqual(response.status_code, 404)

        # test article
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        article = response.json()

        # create
        response = client.post(f'/api/article/{article["id"]}/comment/', {'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        new_comment = response.json()
        self.assertEqual(new_comment['article'], article['id'])
        self.assertEqual(new_comment['content'], 'content')
        self.assertEqual(new_comment['article'], get_user(client).id)

        # retrieve comment
        response = client.get(f'/api/article/{article["id"]}/comment/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0], new_comment)

    def test_comment_get(self):
        client = Client()

        # not get, put, delete
        response = client.options('/api/comment/1/')
        self.assertEqual(response.status_code, 405)

        # not signed in
        response = client.get('/api/comment/1/')
        self.assertEqual(response.status_code, 403)

        # test user
        response = client.post('/api/signup/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # log in
        response = client.post('/api/signin/', {'username': 'user', 'password': 'pass'},
                content_type='application/json')

        # nonexistent
        response = client.get('/api/comment/1/')
        self.assertEqual(response.status_code, 404)

        # test article
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        article = response.json()

        # test comment
        response = client.post(f'/api/article/{article["id"]}/comment/', {'content': 'content'},
                content_type='application/json')
        comment = response.json()

        # retrieve article
        response = client.get(f'/api/comment/{comment["id"]}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), comment)

    def test_comment_put_delete(self):
        client = Client()

        # create test user1
        response = client.post('/api/signup/', {'username': 'user1', 'password': 'pass'},
                content_type='application/json')

        # log in user1
        response = client.post('/api/signin/', {'username': 'user1', 'password': 'pass'},
                content_type='application/json')
        user1 = get_user(client)

        # test article
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        article = response.json()

        # create test comment 1
        response = client.post(f'/api/article/{article["id"]}/comment/', {'content': 'content'},
                content_type='application/json')
        comment1 = response.json()

        client.get('/api/signout/')

        # create test user2
        response = client.post('/api/signup/', {'username': 'user2', 'password': 'pass'},
                content_type='application/json')

        # log in user2
        response = client.post('/api/signin/', {'username': 'user2', 'password': 'pass'},
                content_type='application/json')
        user2 = get_user(client)

        # create test comment 1
        response = client.post(f'/api/article/{article["id"]}/comment/', {'content': 'content'},
                content_type='application/json')
        comment2 = response.json()

        # not same user
        response = client.put(f'/api/comment/{comment1["id"]}/', {})
        self.assertEqual(response.status_code, 403)

        # correct put
        response = client.put(f'/api/comment/{comment2["id"]}/', {'content': 'content2'},
                content_type='application/json')
        self.assertEqual(response.status_code, 200)

        comment2['content'] = 'content2'

        response = client.get(f'/api/comment/{comment2["id"]}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), comment2)

        response = client.delete(f'/api/comment/{comment1["id"]}/')
        self.assertEqual(response.status_code, 403)

        response = client.delete(f'/api/comment/{comment2["id"]}/')
        self.assertEqual(response.status_code, 200)

        # check if deleted
        response = client.get(f'/api/article/{article["id"]}/comment/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0], comment1)
