import requests
from django.http import HttpResponse, JsonResponse
from requests.exceptions import HTTPError
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Product
from .serializers import ProductSerializer


@api_view(['GET'])
def get_product(request, version, id):
    response_object = {
        'status': 'Failed',
        'message': 'Product doesn\'t exist'
    }
    try:
        product = Product.objects.get(id=id)
        print (product)

    except Product.DoesNotExist:
        return JsonResponse(response_object, status=404)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)


@api_view(['GET'])
def get_products(request, version):
    response_object = {
        'status': 'Failed',
        'message': ''
    }
    try:
        response = requests.get('http://localhost:8000/v1/param')
        if not response:
            response_object['message'] = 'Failed to get params.'
            return JsonResponse(response_object, status=404)

        id = response.json()['id']
        
        products = Product.objects.filter(school_year=id)

    except Product.DoesNotExist:
        response_object['message'] = 'Product doesn\'t exist.'
        return JsonResponse(response_object, status=404)

    if request.method == 'GET':
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def get_products_all(request, version):
    response_object = {
        'status': 'Failed',
        'message': 'Product doesn\'t exist'
    }
    try:
        products = Product.objects.all()
    
    except Product.DoesNotExist:
        return JsonResponse(response_object, status=404)

    if request.method == 'GET':
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
