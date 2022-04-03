from rest_framework import serializers
from .models import Family, Record, CAF, Health, Sibling, SiblingChild, SiblingIntels


class IntelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiblingIntels
        fields = '__all__'
        # fields = ['quotient_1', 'quotient_2', 'recipent_number', 'school_year']


class SiblingChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiblingChild
        fields = '__all__'


class SiblingSerializer(serializers.ModelSerializer):
    siblings = SiblingChildSerializer(many=True, read_only=True)

    class Meta:
        model = Sibling
        fields = ('id', 'parent', 'siblings')


class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ("parent", "child")


class CAFSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAF
        fields = '__all__'


class HealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Health
        fields = '__all__'


class RecordSerializer(serializers.ModelSerializer):
    caf = CAFSerializer(read_only=True)
    health = HealthSerializer(read_only=True)

    class Meta:
        model = Record
        fields = '__all__'


class CAFSerializerShort(serializers.ModelSerializer):
    class Meta:
        model = CAF
        fields = ['quotient_q1', 'quotient_q2']


class RecordSerializerShort(serializers.ModelSerializer):
    caf = CAFSerializerShort(read_only=True)

    class Meta:
        model = Record
        fields = ['id', 'school', 'classroom', 'child_id', 'caf']
