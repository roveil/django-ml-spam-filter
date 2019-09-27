from django.conf.urls import url

from spam_filter import views

urlpatterns = [
    url(r'^check/?$', views.CheckHandler.as_view()),
    url(r'^learn/?$', views.LearnHandler.as_view())
]
