from rest_framework import serializers

from .models import Product, SchoolYear


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class SchoolYearSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = SchoolYear
        # fields = '__all__'
        fields = ['id', 'date_start', 'date_end', 'is_active', 'products']


class SimpleSchoolYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolYear
        fields = '__all__'
