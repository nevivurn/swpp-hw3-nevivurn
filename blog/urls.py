from django.urls import path
from blog import views

# TODO: REMOVE, ONLY FOR DEBUGGING
#from django.views.decorators.csrf import csrf_exempt

# TODO: used during testing, since it needs to be actually on
def csrf_exempt(i): return i

urlpatterns = [
    path('signup/', csrf_exempt(views.signup), name='signup'),
    path('signin/', csrf_exempt(views.signin), name='signin'),
    path('signout/', csrf_exempt(views.signout), name='signout'),
    path('article/', csrf_exempt(views.articles), name='articles'),
    path('article/<int:aid>/', csrf_exempt(views.article), name='article'),
    path('token/', csrf_exempt(views.token), name='token'),
]
