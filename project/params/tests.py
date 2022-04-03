import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

# Create your tests here.


class BaseTestView(APITestCase):
    client = APIClient()

    def setUp(self):
        return None

class ParamsGetTests(BaseTestView):
    pass