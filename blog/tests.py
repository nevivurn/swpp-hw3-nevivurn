from django.test import TestCase, Client
from django.contrib.auth import get_user
import json

class BlogTestCase(TestCase):
    def test_csrf(self):
        # By default, csrf checks are disabled in test client
        # To test csrf protection we enforce csrf checks here
        client = Client(enforce_csrf_checks=True)
        response = client.post('/api/signup/', {'username': 'chris', 'password': 'chris'},
                content_type='application/json')
        self.assertEqual(response.status_code, 403)  # Request without csrf token returns 403 response

        response = client.get('/api/token/')
        csrftoken = response.cookies['csrftoken'].value  # Get csrf token from cookie

        response = client.post('/api/signup/', {'username': 'chris', 'password': 'chris'},
                content_type='application/json', HTTP_X_CSRFTOKEN=csrftoken)
        self.assertEqual(response.status_code, 201)  # Pass csrf protection

    def test_token_post(self):
        client = Client()
        response = client.post('/api/token/', {})
        self.assertEqual(response.status_code, 405)

    def test_signup_validation(self):
        client = Client()

        # non-json
        response = client.post('/api/signup/', 'not_json', content_type='text/plain')
        self.assertEqual(response.status_code, 400)

        # extra keys
        response = client.post('/api/signup/', {'username': 'validity_user', 'password': 'pass', 'extra': 'field'},
                content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # not post
        response = client.get('/api/signup/')
        self.assertEqual(response.status_code, 405)

    def test_signup_duplicate(self):
        client = Client()

        # first user
        resposne = client.post('/api/signup/', {'username': 'dup_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(resposne.status_code, 201)

        # recreate
        resposne = client.post('/api/signup/', {'username': 'dup_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(resposne.status_code, 400)

    def test_signin_validation(self):
        client = Client()

        # non-json
        response = client.post('/api/signin/', 'not_json', content_type='text/plain')
        self.assertEqual(response.status_code, 400)

        # extra keys
        response = client.post('/api/signin/', {'username': 'validity_user', 'password': 'pass', 'extra': 'field'},
                content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # not post
        response = client.get('/api/signin/')
        self.assertEqual(response.status_code, 405)

    def test_signin(self):
        client = Client()

        # create test user
        response = client.post('/api/signup/', {'username': 'signin_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # try with incorrect password
        response = client.post('/api/signin/', {'username': 'signin_test_user', 'password': 'incorrect'},
                content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(get_user(client).is_authenticated)

        # try with correct password
        response = client.post('/api/signin/', {'username': 'signin_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)

    def test_signout(self):
        client = Client()

        # only gets allowed
        response = client.options('/api/signout/')
        self.assertEqual(response.status_code, 405)

        # create test user
        response = client.post('/api/signup/', {'username': 'signout_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in
        response = client.post('/api/signin/', {'username': 'signout_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)

        response = client.get('/api/signout/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(get_user(client).is_authenticated)

        # signout while signed out is an error
        response = client.get('/api/signout/')
        self.assertEqual(response.status_code, 401)

    def test_articles_list_validation(self):
        client = Client()

        response = client.options('/api/article/')
        self.assertEqual(response.status_code, 405)

        response = client.get('/api/article/')
        self.assertEqual(response.status_code, 403)

    def test_articles_post_validation(self):
        client = Client()

        response = client.post('/api/article/')
        self.assertEqual(response.status_code, 403)

        # create test user
        response = client.post('/api/signup/', {'username': 'articles_test_validate', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in
        response = client.post('/api/signin/', {'username': 'articles_test_validate', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)

        # invalid: missing fields
        response = client.post('/api/article/', {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # invalid: extra fields
        response = client.post('/api/article/', {'title': 'title', 'content': 'content', 'extra': 'field'},
                content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # valid
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        new_article = response.json()
        self.assertEqual(new_article['title'], 'title')
        self.assertEqual(new_article['content'], 'content')
        self.assertEqual(new_article['author'], get_user(client).id)

        response = client.get('/api/article/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0], new_article)

    def test_article_get(self):
        client = Client()

        response = client.options('/api/article/1/')
        self.assertEqual(response.status_code, 405)

        response = client.get('/api/article/1/')
        self.assertEqual(response.status_code, 403)

        # create test user
        response = client.post('/api/signup/', {'username': 'article_get_test', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in
        response = client.post('/api/signin/', {'username': 'article_get_test', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)

        # nonexistent
        response = client.get('/api/article/1/')
        self.assertEqual(response.status_code, 404)

        # create test article
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        article = response.json()

        response = client.get('/api/article/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), article)

    def test_article_put(self):
        client = Client()

        # create test user1
        response = client.post('/api/signup/', {'username': 'article_put_test1', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in user1
        response = client.post('/api/signin/', {'username': 'article_put_test1', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)
        user1 = get_user(client)

        # create test article1
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        article1 = response.json()

        client.get('/api/signout/')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(get_user(client).is_authenticated)

        # create test user2
        response = client.post('/api/signup/', {'username': 'article_put_test2', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in user2
        response = client.post('/api/signin/', {'username': 'article_put_test2', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)
        user2 = get_user(client)

        # create test article2
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        article2 = response.json()

        response = client.put(f'/api/article/{article1["id"]}/', {})
        self.assertEqual(response.status_code, 403)

        response = client.put(f'/api/article/{article2["id"]}/', {})
        self.assertEqual(response.status_code, 400)

        response = client.put(f'/api/article/{article2["id"]}/', {'title': 'title1', 'content': 'content1', 'extra': 'field'},
                content_type='application/json')
        self.assertEqual(response.status_code, 400)

        response = client.put(f'/api/article/{article2["id"]}/', {'title': 'title1', 'content': 'content1'},
                content_type='application/json')
        self.assertEqual(response.status_code, 200)

        article2['title'] = 'title1'
        article2['content'] = 'content1'

        response = client.get(f'/api/article/{article2["id"]}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), article2)

    def test_article_delete(self):
        client = Client()

        # create test user1
        response = client.post('/api/signup/', {'username': 'article_put_test1', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in user1
        response = client.post('/api/signin/', {'username': 'article_put_test1', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)
        user1 = get_user(client)

        # create test article1
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        article1 = response.json()

        client.get('/api/signout/')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(get_user(client).is_authenticated)

        # create test user2
        response = client.post('/api/signup/', {'username': 'article_put_test2', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in user2
        response = client.post('/api/signin/', {'username': 'article_put_test2', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(get_user(client).is_authenticated)
        user2 = get_user(client)

        # create test article2
        response = client.post('/api/article/', {'title': 'title', 'content': 'content'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        article2 = response.json()

        response = client.delete(f'/api/article/{article1["id"]}/')
        self.assertEqual(response.status_code, 403)

        response = client.delete(f'/api/article/{article2["id"]}/')
        self.assertEqual(response.status_code, 200)
