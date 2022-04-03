import json

from django.urls import reverse
from django.http.request import QueryDict
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from .models import Client, ClientCredit, Order, OrderMethod, OrderStatus, Ticket, TicketStatus, StatusEnum
from .serializers import OrderSerializer

# from .utils import verify_order

from users.models import User, UserAuth, Role
from params.models import Product, SchoolYear
from registration.models import Sibling, SiblingChild



class BaseViewTest(APITestCase):
    client = APIClient()

    def setUp(self):
        # add test data
        return None

