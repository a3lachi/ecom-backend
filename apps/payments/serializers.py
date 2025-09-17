from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Payment, PaymentMethod, PaymentTransaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'provider', 'display_name', 'is_active',
            'logo_url', 'description', 'sort_order'
        ]
        # Exclude sensitive configuration data


class CreatePaymentSerializer(serializers.Serializer):
    payment_method = serializers.CharField(
        help_text="Payment method provider (PAYPAL, CAIXA, BIZUM, BINANCE_PAY)"
    )
    shipping_address = serializers.DictField(
        required=False,
        help_text="Shipping address information",
        child=serializers.CharField()
    )
    billing_address = serializers.DictField(
        required=False,
        help_text="Billing address information (optional, defaults to shipping)",
        child=serializers.CharField()
    )

    def validate_shipping_address(self, value):
        """Validate required shipping address fields"""
        required_fields = ['first_name', 'last_name', 'address_line_1', 'city', 'state_province', 'postal_code', 'country']
        
        for field in required_fields:
            if not value.get(field):
                raise serializers.ValidationError(f"Shipping address field '{field}' is required")
        
        return value

    def validate_payment_method(self, value):
        try:
            payment_method = PaymentMethod.objects.get(
                provider=value.upper(),
                is_active=True
            )
            return payment_method
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method not available")


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='payment_method.display_name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    is_successful = serializers.ReadOnlyField()
    is_refundable = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Payment
        fields = [
            'payment_id', 'order', 'order_number', 'payment_method', 'payment_method_name',
            'status', 'payment_type', 'amount', 'currency',
            'provider_transaction_id', 'success_url', 'cancel_url',
            'created_at', 'updated_at', 'processed_at', 'expires_at',
            'failure_reason', 'notes', 'is_successful', 'is_refundable', 'can_be_cancelled'
        ]
        read_only_fields = [
            'payment_id', 'status', 'provider_transaction_id',
            'created_at', 'updated_at', 'processed_at', 'expires_at',
            'failure_reason'
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'action', 'amount', 'provider_transaction_id',
            'success', 'error_message', 'notes', 'created_at'
        ]


class PaymentDetailSerializer(PaymentSerializer):
    transactions = PaymentTransactionSerializer(many=True, read_only=True)
    
    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ['transactions', 'provider_response']