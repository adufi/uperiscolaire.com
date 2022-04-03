from rest_framework import serializers
from .models import Order, Ticket, OrderMethod, OrderStatus, TicketStatus


class TicketStatusSerializers(serializers.ModelSerializer):
    class Meta:
        model = TicketStatus
        fields = '__all__'


""" For OrderSerializer """
class _TicketSerializer(serializers.ModelSerializer):
    status = TicketStatusSerializers(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'

class OrderStatusSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = '__all__'


class MethodSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrderMethod
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializers(many=True, read_only=True)
    tickets = _TicketSerializer(many = True, read_only=True)
    methods = MethodSerializers(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        # fields = ['tickets']


""" """
class OrderIDSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Order
        fields = ['id']

        
""" Call alone  """
class TicketSerializer(serializers.ModelSerializer):

    # order = OrderIDSerializer(read_only=True, source='order_id')
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    status = TicketStatusSerializers(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'payee', 'product', 'status', 'order']