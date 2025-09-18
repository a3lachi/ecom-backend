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


class AddressSerializer(serializers.Serializer):
    """Serializer for address fields in payment creation"""
    first_name = serializers.CharField(max_length=100, help_text="First name")
    last_name = serializers.CharField(max_length=100, help_text="Last name")
    company = serializers.CharField(max_length=100, required=False, help_text="Company name (optional)")
    address_line_1 = serializers.CharField(max_length=255, help_text="Address line 1")
    address_line_2 = serializers.CharField(max_length=255, required=False, help_text="Address line 2 (optional)")
    city = serializers.CharField(max_length=100, help_text="City")
    state_province = serializers.CharField(max_length=100, help_text="State or province")
    postal_code = serializers.CharField(max_length=20, help_text="Postal/ZIP code")
    country = serializers.CharField(max_length=100, help_text="Country")
    phone = serializers.CharField(max_length=20, required=False, help_text="Phone number (optional)")


class CreatePaymentSerializer(serializers.Serializer):
    payment_method = serializers.CharField(
        help_text="Payment method provider (PAYPAL, CAIXA, BIZUM, BINANCE_PAY)"
    )
    shipping_address = AddressSerializer(
        required=True,
        help_text="Shipping address information"
    )
    billing_address = AddressSerializer(
        required=False,
        help_text="Billing address information (optional, defaults to shipping)"
    )

    def validate(self, data):
        """Validate the entire payload"""
        # The AddressSerializer will handle validation of individual fields
        # We can add any cross-field validation here if needed
        return data

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