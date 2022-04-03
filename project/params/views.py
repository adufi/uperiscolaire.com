from django.http import HttpResponse, JsonResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from users.decorators import login_required_view

from .forms import ProductForm
from .utils import check_authorizations, get_parsed_data
from .models import SchoolYear, Product, CategoryEnum, SubCategoryEnum
from .serializers import SchoolYearSerializer, SimpleSchoolYearSerializer, ProductSerializer


class ListParamsView(generics.ListAPIView):
    """
    Provides a get method handler.
    """
    queryset = SchoolYear.objects.all()
    serializer_class = SchoolYearSerializer

""" Old """
@api_view(['GET'])
def get_param(request, version):
    try:
        sys = SchoolYear.objects.all()
        for sy in sys:
            if sy.is_active() and request.method == 'GET':
                serializer = SimpleSchoolYearSerializer(sy)
                return Response(serializer.data)

    except SchoolYear.DoesNotExist:
        return HttpResponse(status=404)
    return HttpResponse(status=404)


""" Old """
@api_view(['GET'])
def get_param_details(request, version):
    try:
        sys = SchoolYear.objects.all()
        for sy in sys:
            if sy.is_active() and request.method == 'GET':
                serializer = SchoolYearSerializer(sy)
                return Response(serializer.data)

    except SchoolYear.DoesNotExist:
        return HttpResponse(status=404)
    return HttpResponse(status=404)


""" Old """
@api_view(['GET'])
def get_param_by_id(request, version, id):
    try:
        sy = SchoolYear.objects.filter(id=id)
    except SchoolYear.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = SchoolYearSerializer(sy, many=True)
        return Response(serializer.data)



@api_view(['GET', 'POST'])
def params(request, version):
    if request.method == 'GET':
        response_object = {
            'status': 'Failure'
        }
        try:
            sys = SchoolYear.objects.all()
            for sy in sys:
                if sy.is_active():
                    serializer = SimpleSchoolYearSerializer(sy)
                    response_object['status'] = 'Success'
                    response_object['school_year'] = serializer.data
                    return JsonResponse(response_object, status=status.HTTP_200_OK)

        except SchoolYear.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        response_object = {
            'status': 'Failure'
        }
        s = check_authorizations(request.headers, ['admin'])
        if type(s) is str:
            print ('Error: ' + s)
            response_object['message'] = 'You are not allowed to access this ressource.'
            return JsonResponse(response_object, status=status.HTTP_401_UNAUTHORIZED)
        
        data = get_parsed_data(request.data)
        if not data:
            response_object['message'] = 'Failed to get data.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        s = create_schoolyear(data)
        if type(s) is str:
            response_object['message'] = f'Invalid payload with error: {s}.'
            return JsonResponse(response_object, status=status.HTTP_400_BAD_REQUEST)

        response_object['status'] = 'Success'
        return JsonResponse(response_object, status=status.HTTP_200_OK)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def params_all(request, version):
    if request.method == 'GET':
        response_object = {
            'status': 'Failure'
        }
        try:
            sys = SchoolYear.objects.all()
            serializer = SimpleSchoolYearSerializer(sys, many=True)
            response_object['status'] = 'Success'
            response_object['school_years'] = serializer.data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        except SchoolYear.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def params_id(request, version, id):
    if request.method == 'GET':
        response_object = {
            'status': 'Failure'
        }
        try:
            sy = SchoolYear.objects.get(id=id)
            serializer = SimpleSchoolYearSerializer(sy)
            response_object['status'] = 'Success'
            response_object['school_year'] = serializer.data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        except SchoolYear.DoesNotExist:
            response_object['message'] = 'School Year doesn\'t exist.'
            return JsonResponse(response_object,status=status.HTTP_404_NOT_FOUND)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def params_details(request, version):
    if request.method == 'GET':
        response_object = {
            'status': 'Failure'
        }
        try:
            sys = SchoolYear.objects.all()
            for sy in sys:
                if sy.is_active():
                    serializer = SchoolYearSerializer(sy)
                    response_object['status'] = 'Success'
                    response_object['school_year'] = serializer.data
                    return JsonResponse(response_object, status=status.HTTP_200_OK)

        except SchoolYear.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def params_details_all(request, version):
    if request.method == 'GET':
        response_object = {
            'status': 'Failure'
        }
        try:
            sys = SchoolYear.objects.all()
            serializer = SchoolYearSerializer(sys, many=True)
            response_object['status'] = 'Success'
            response_object['school_years'] = serializer.data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        except SchoolYear.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def params_details_id(request, version, id):
    if request.method == 'GET':
        response_object = {
            'status': 'Failure'
        }
        try:
            sy = SchoolYear.objects.get(id=id)
            serializer = SchoolYearSerializer(sy)
            response_object['status'] = 'Success'
            response_object['school_year'] = serializer.data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        except SchoolYear.DoesNotExist:
            response_object['message'] = 'School Year doesn\'t exist.'
            return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def params_product_id(request, version, id):
    response_object = {
        'status': 'Failure'
    }
    try:
        p = Product.objects.get(id=id)
        if p:
            serialized_data = ProductSerializer(p).data

            response_object['status'] = 'Success'
            response_object['product'] = serialized_data
            return JsonResponse(response_object, status=status.HTTP_200_OK)

        response_object['message'] = 'Failed to get the product.'

    except (Product.DoesNotExist):
        response_object['message'] = 'Product does not exist.'
    
    return JsonResponse(response_object, status=status.HTTP_404_NOT_FOUND)


""" Release 1.0.4 """
""" 06 Avril 2021 """

def api_v2_product_active (request):
    try:
        school_year = SchoolYear.objects.get(is_active=True)
        return JsonResponse({
                'status': 'Success',
                'school_year': SchoolYearSerializer(school_year).data
            }, status=status.HTTP_200_OK
        )
    except:
        return JsonResponse({
                'status': 'Failure',
                'message': 'Objet introuvable.'
            }, status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def api_v2_school_year_active (request):
    try:
        school_year = SchoolYear.objects.get(is_active=True)
        return JsonResponse({
                'status': 'Success',
                'school_year': SimpleSchoolYearSerializer(school_year).data
            }, status=status.HTTP_200_OK
        )
    except:
        return JsonResponse({
                'status': 'Failure',
                'message': 'Objet introuvable.'
            }, status=status.HTTP_404_NOT_FOUND
        )

class SchoolYearList (APIView):

    def get (self, request):
        school_years = SchoolYear.objects.all()

        products = request.GET.get('products', None)
        if products:
            serializer = SchoolYearSerializer(school_years, many=True)
        else:
            serializer = SimpleSchoolYearSerializer(school_years, many=True)

        return JsonResponse({
                'status': 'Success',
                'school_years': serializer.data
            }, status=status.HTTP_200_OK
        )


class SchoolYearDetail (APIView):

    def get (self, request, pk):
        try:
            school_year =  SchoolYear.objects.get(pk=pk)
            return JsonResponse({
                'status': 'Success',
                'school_year': SimpleSchoolYearSerializer(school_year).data
            }, status=status.HTTP_200_OK
        )
            
        except SchoolYear.DoesNotExist:
            return JsonResponse({
                    'status': 'Failure',
                    'message': 'Objet introuvable.'
                }, status=status.HTTP_404_NOT_FOUND
            )


"""
GET     /api/v2/products                - List products
GET     /api/v2/products?school_year    - List products by school_year
"""
class ProductList (APIView):

    def get (self, request):
        products = Product.objects.all()

        school_year = request.GET.get('school_year', None)
        if school_year:
            products = products.filter(school_year__pk=school_year)

        return JsonResponse({
                'status': 'Success',
                'products': ProductSerializer(products, many=True).data
            }, status=status.HTTP_200_OK
        )

    """ Create or Update products """
    @login_required_view(['is_superuser', 'admin'])
    def post (self, request):
        summary = []
        correct = False
        products = []

        for data in request.data:
            product = None

            if 'id' in data:
                product = Product.objects.filter(pk=data['id'])

            form = ProductForm(data or None, instance=product or None)
            if form.is_valid():
                products.append(
                    form.save()
                )
                
                summary.append(f'Le produit {data["name"]} a bien été créé/mis à jour.')
                correct = True

            else:
                print (form.errors)
                summary.append(f'Erreur, le produit {data["name"]} n\'a pas été créé/mis à jour.')

        if correct:
            return JsonResponse({
                    'status': 'Success',
                    'summary': summary,
                    'products': ProductSerializer(products, many=True).data
                }, status=status.HTTP_200_OK
            )

        else:
            return JsonResponse({
                    'status': 'Failure',
                    'message': 'Aucun produit n\'a été créé ou mis à jour.'
                }, status=status.HTTP_400_BAD_REQUEST
            )


"""
GET     Get product by ID
"""
class ProductDetail (APIView):

    def get (self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            return JsonResponse({
                    'status': 'Success',
                    'products': ProductSerializer(product).data
                }, status=status.HTTP_200_OK
            )
            
        except Product.DoesNotExist:
            return JsonResponse({
                    'status': 'Failure',
                    'message': 'Objet introuvable.'
                }, status=status.HTTP_404_NOT_FOUND
            )
            
    @login_required_view(['is_superuser', 'admin'])
    def put (self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            
        except Product.DoesNotExist:
            return JsonResponse({
                    'status': 'Failure',
                    'message': 'Objet introuvable.'
                }, status=status.HTTP_404_NOT_FOUND
            )

        form = ProductForm(request.data or None, instance=product)

        if form.is_valid():
            form.save()
            return JsonResponse({
                    'status': 'Success',
                    'product': ProductSerializer(product).data

                }, status=status.HTTP_200_OK
            )

        return JsonResponse({
                'status': 'Failure',
                'message': 'Payload invalid.',
                'errors': form.errors.as_json()
            }, status=status.HTTP_400_BAD_REQUEST
        )

    @login_required_view(['is_superuser', 'admin'])
    def delete (self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            
        except Product.DoesNotExist:
            return JsonResponse({
                    'status': 'Failure',
                    'message': 'Objet introuvable.'
                }, status=status.HTTP_404_NOT_FOUND
            )

        product.delete()

        return JsonResponse({
                'status': 'Success'
            }, status=status.HTTP_200_OK
        )
