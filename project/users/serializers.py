from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import *


class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = ['email']


class AuthSerializerWithToken(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    # password = serializers.CharField(write_only=True)
    
    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def create(self, validated_data):
        # password = validated_data.pop('password', None)
        pass

    class Meta:
        model = UserAuth
        fields = ['email', 'token']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        # fields = ['name', 'slug']


class RoleSerializerShort(serializers.ModelSerializer):
    class Meta:
        model = Role
        # fields = '__all__'
        fields = ['name']


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEmail
        fields = '__all__'


""" Old """
class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhone
        fields = '__all__'


class PhonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhones
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    auth = AuthSerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    emails = EmailSerializer(many=True, read_only=True)
    phones = PhonesSerializer(read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = '__all__'


class UserSerializerShort(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'dob']


class _UserSerializer(serializers.ModelSerializer):
    auth = AuthSerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    emails = EmailSerializer(many=True, read_only=True)
    phones = PhoneSerializer(many=True, read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = '__all__'
