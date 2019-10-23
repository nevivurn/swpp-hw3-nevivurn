from django.test import TestCase, Client
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

    def test_signin_invalid(self):
        client = Client()

        # create test user
        response = client.post('/api/signup/', {'username': 'signin_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # try with incorrect password
        response = client.post('/api/signin/', {'username': 'signin_test_user', 'password': 'incorrect'},
                content_type='application/json')
        self.assertEqual(response.status_code, 401)

        # try with correct password
        response = client.post('/api/signin/', {'username': 'signin_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)

    def test_signout(self):
        client = Client()

        # only gets allowed
        response = client.post('/api/signout/', {})
        self.assertEqual(response.status_code, 405)

        # create test user
        response = client.post('/api/signup/', {'username': 'signout_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # log in
        response = client.post('/api/signin/', {'username': 'signout_test_user', 'password': 'pass'},
                content_type='application/json')
        self.assertEqual(response.status_code, 204)

        response = client.get('/api/signout/')
        self.assertEqual(response.status_code, 204)

        # signout while signed out is an error
        response = client.get('/api/signout/')
        self.assertEqual(response.status_code, 401)
