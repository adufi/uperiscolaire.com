from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from .models import Product
from .serializers import ProductSerializer

# Create your tests here.

class BaseViewTest(APITestCase):
    client = APIClient()

    @staticmethod
    def create_product(school_year = 2, name='', desc='', slug='', price=0, category='', subcategory='', stock_cur=0, stock_max=0):
        return Product.objects.create(
            name=name,
            desc=desc,
            slug=slug,
            price=price,
            category=category,
            subcategory=subcategory,
            stock_cur=stock_cur,
            stock_max=stock_max,
            school_year=2
        )

    def setUp(self):
        # add test data
        pass


class ProductTest(BaseViewTest):

    def test_product(self):
        p = self.create_product(
            name='Septembre', slug='sept_01_2019x2020', desc='Periscolaire',
            category='peri', subcategory='sept',
            price=20,
            school_year=2
        )

        response = self.client.get(
            reverse(f'product', kwargs={'version': 'v1', 'id': p.id})
        )

        serialized = ProductSerializer(p)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # with self.client:

    def test_product_invalid_id(self):
        response = self.client.get(
            reverse(f'product', kwargs={'version': 'v1', 'id': 0})
        )
        json = response.json()
        self.assertEqual(json['status'], 'Failed')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_products(self):
        self.create_product(
            name='Septembre', slug='sept_01_2019x2020', desc='Periscolaire',
            category='peri', subcategory='sept',
            price=20,
            school_year=1
        )
        self.create_product(
            name='Septembre', slug='sept_01_2019x2020', desc='Periscolaire',
            category='peri', subcategory='sept',
            price=20,
            school_year=2
        )

        response = self.client.get(
            reverse(f'products', kwargs={'version': 'v1'})
        )

        expected = Product.objects.filter(school_year=2)
        serialized = ProductSerializer(expected, many = True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_products_all(self):
        self.create_product(
            name='Septembre', slug='sept_01_2019x2020', desc='Periscolaire',
            category='peri', subcategory='sept',
            price=20,
            school_year=1
        )
        self.create_product(
            name='Septembre', slug='sept_01_2019x2020', desc='Periscolaire',
            category='peri', subcategory='sept',
            price=20,
            school_year=2
        )

        response = self.client.get(
            reverse(f'products', kwargs={'version': 'v1'})
        )

        expected = Product.objects.all()
        serialized = ProductSerializer(expected, many=True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
