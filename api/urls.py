from django.conf.urls import url, include
from django.urls import path
from rest_framework import routers

from api import views

router = routers.SimpleRouter()

router.register(
    'media',
    views.MediaViewSet,
    base_name='media',
)

urlpatterns = [
]

urlpatterns += router.urls
