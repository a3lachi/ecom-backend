from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import logging

from .models import Payment, PaymentMethod, PaymentTransaction, PaymentWebhook
from .serializers import (
    CreatePaymentSerializer, PaymentSerializer, PaymentMethodSerializer,
    PaymentDetailSerializer
)
from .paypal import create_order, capture_order, PayPalError, verify_webhook
from .caixa import create_payment_form, process_webhook_response, CaixaError

logger = logging.getLogger(__name__)


@extend_schema(
    summary="List Payment Methods",
    description="Get all available payment methods for checkout",
    responses={
        200: PaymentMethodSerializer(many=True),
        401: {
            'description': 'Authentication required',
            'examples': {
                'application/json': {
                    'detail': 'Authentication credentials were not provided.'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_payment_methods(request):
    """List all available payment methods."""
    try:
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('sort_order')
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error listing payment methods: {e}")
        return Response(
            {'error': 'Failed to retrieve payment methods'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Create Payment from Cart",
    description="Create a new payment from user's cart. Creates an order and payment in one step. Returns payment details and approval URL for redirect-based payments like PayPal.",
    request=CreatePaymentSerializer,
    responses={
        201: {
            'description': 'Payment created successfully',
            'examples': {
                'application/json': {
                    'payment_id': 'PAY-20250916-ABC123456789',
                    'status': 'PROCESSING',
                    'approval_url': 'https://www.sandbox.paypal.com/checkoutnow?token=ABC123',
                    'amount': '99.99',
                    'currency': 'USD',
                    'provider': 'PayPal',
                    'message': 'PayPal payment created successfully',
                    'next_action': 'redirect_to_approval_url'
                }
            }
        },
        400: {
            'description': 'Validation error',
            'examples': {
                'application/json': {
                    'error': 'No active cart found'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    """Create a new payment from cart checkout."""
    try:
        serializer = CreatePaymentSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        payment_method = data['payment_method']
        shipping_address = data.get('shipping_address', {})
        billing_address = data.get('billing_address', shipping_address)
        
        # Get user's active cart
        from apps.cart.models import Cart
        try:
            cart = Cart.objects.get(user=request.user, status=Cart.Status.ACTIVE)
        except Cart.DoesNotExist:
            return Response(
                {'error': 'No active cart found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate cart has items
        if cart.items_count == 0:
            return Response(
                {'error': 'Cart is empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create order from cart
            order = _create_order_from_cart(cart, shipping_address, billing_address)
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                payment_method=payment_method,
                amount=order.grand_total,
                currency=order.currency
            )
            
            try:
                # Handle different payment methods
                if payment_method.provider == PaymentMethod.Provider.PAYPAL:
                    return _handle_paypal_payment(payment, request, cart)
                elif payment_method.provider == PaymentMethod.Provider.CAIXA:
                    return _handle_caixa_payment(payment, request, cart, shipping_address)
                else:
                    # For other payment methods, create basic transaction and return info
                    PaymentTransaction.objects.create(
                        payment=payment,
                        action=PaymentTransaction.Action.CREATED,
                        amount=payment.amount,
                        success=True,
                        notes=f"{payment_method.display_name} payment created"
                    )
                    
                    payment_serializer = PaymentSerializer(payment, context={'request': request})
                    return Response({
                        **payment_serializer.data,
                        'message': f'{payment_method.display_name} payment created',
                        'next_action': 'redirect_to_provider'
                    }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                # Payment creation failed - revert cart and cleanup
                logger.error(f"Payment creation failed, reverting cart: {e}")
                cart.status = cart.Status.ACTIVE
                cart.save()
                
                # Delete the order since payment failed
                order.delete()
                
                # Re-raise the exception to return error to user
                raise
                
    except Exception as e:
        logger.error(f"Payment creation error: {e}")
        return Response(
            {'error': 'Failed to create payment'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _create_order_from_cart(cart, shipping_address, billing_address):
    """Create an order from cart items and address information."""
    from apps.orders.models import Order, OrderItem, OrderAddress
    
    # Create the order
    order = Order.objects.create(
        user=cart.user,
        currency=cart.currency,
        items_subtotal=cart.items_subtotal,
        discount_total=cart.discount_total,
        shipping_total=cart.shipping_total,
        tax_total=cart.tax_total,
        grand_total=cart.grand_total,
        notes="Created from cart checkout"
    )
    
    # Create order items from cart items
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            color=cart_item.color,
            size=cart_item.size,
            quantity=cart_item.quantity,
            product_name_snapshot=cart_item.product_name_snapshot,
            sku_snapshot=cart_item.sku_snapshot,
            unit_price_snapshot=cart_item.unit_price_snapshot,
            compare_price_snapshot=cart_item.compare_price_snapshot,
            image_url_snapshot=cart_item.image_url_snapshot
        )
    
    # Create shipping address
    if shipping_address:
        OrderAddress.objects.create(
            order=order,
            address_type=OrderAddress.AddressType.SHIPPING,
            first_name=shipping_address.get('first_name', ''),
            last_name=shipping_address.get('last_name', ''),
            company=shipping_address.get('company', ''),
            address_line_1=shipping_address.get('address_line_1', ''),
            address_line_2=shipping_address.get('address_line_2', ''),
            city=shipping_address.get('city', ''),
            state_province=shipping_address.get('state_province', ''),
            postal_code=shipping_address.get('postal_code', ''),
            country=shipping_address.get('country', ''),
            phone=shipping_address.get('phone', '')
        )
    
    # Create billing address (use shipping if not provided)
    if billing_address:
        OrderAddress.objects.create(
            order=order,
            address_type=OrderAddress.AddressType.BILLING,
            first_name=billing_address.get('first_name', ''),
            last_name=billing_address.get('last_name', ''),
            company=billing_address.get('company', ''),
            address_line_1=billing_address.get('address_line_1', ''),
            address_line_2=billing_address.get('address_line_2', ''),
            city=billing_address.get('city', ''),
            state_province=billing_address.get('state_province', ''),
            postal_code=billing_address.get('postal_code', ''),
            country=billing_address.get('country', ''),
            phone=billing_address.get('phone', '')
        )
    
    # Mark cart as converted
    cart.status = cart.Status.CONVERTED
    cart.save()
    
    return order


def _handle_paypal_payment(payment, request, cart):
    """Handle PayPal payment creation."""
    # Generate callback URLs automatically
    base_url = f"{request.scheme}://{request.get_host()}"
    return_url = f"{base_url}/api/v1/payments/paypal/success/"
    cancel_url = f"{base_url}/api/v1/payments/paypal/cancel/"
    
    try:
        # Create PayPal order
        paypal_response = create_order(
            amount=float(payment.amount),
            currency=payment.currency,
            order_number=payment.order.order_number,
            return_url=return_url,
            cancel_url=cancel_url
        )
        
        # Update payment with PayPal order ID and callback URLs
        payment.provider_transaction_id = paypal_response['id']
        payment.provider_response = paypal_response
        payment.success_url = return_url
        payment.cancel_url = cancel_url
        payment.status = Payment.Status.PROCESSING
        payment.save()
        
        # Create PayPal order creation transaction
        PaymentTransaction.objects.create(
            payment=payment,
            action=PaymentTransaction.Action.CREATED,
            amount=payment.amount,
            provider_transaction_id=paypal_response['id'],
            provider_response=paypal_response,
            success=True,
            notes="PayPal order created successfully"
        )
        
        # Find approval URL
        approval_url = None
        for link in paypal_response.get('links', []):
            if link.get('rel') == 'approve':
                approval_url = link.get('href')
                break
        
        logger.info(f"PayPal payment created: {payment.payment_id}")
        
        return Response({
            'payment_id': payment.payment_id,
            'status': payment.status,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'provider': 'PayPal',
            'approval_url': approval_url,
            'paypal_order_id': paypal_response['id'],
            'message': 'PayPal payment created successfully',
            'next_action': 'redirect_to_approval_url'
        }, status=status.HTTP_201_CREATED)
        
    except PayPalError as e:
        logger.error(f"PayPal payment creation error: {e}")
        
        # Update payment status
        payment.status = Payment.Status.FAILED
        payment.failure_reason = str(e)
        payment.save()
        
        # Create failed transaction
        PaymentTransaction.objects.create(
            payment=payment,
            action=PaymentTransaction.Action.FAILED,
            success=False,
            error_message=str(e),
            notes="PayPal order creation failed"
        )
        
        # PayPal creation failed - this will trigger cart reversion in calling function
        raise PayPalError(f'PayPal payment creation failed: {e}')


def _handle_caixa_payment(payment, request, cart, shipping_address):
    """Handle CaixaBank payment creation."""
    # Generate callback URLs automatically
    base_url = f"{request.scheme}://{request.get_host()}"
    merchant_url = f"{base_url}/api/v1/payments/caixa/webhook/"
    success_url = f"{base_url}/api/v1/payments/caixa/success/"
    error_url = f"{base_url}/api/v1/payments/caixa/error/"
    
    # Get customer name from shipping address
    customer_name = None
    if shipping_address:
        first_name = shipping_address.get('first_name', '')
        last_name = shipping_address.get('last_name', '')
        if first_name or last_name:
            customer_name = f"{first_name} {last_name}".strip()
    
    try:
        # Create CaixaBank payment form
        form_data = create_payment_form(
            amount=float(payment.amount),
            order_number=payment.order.order_number,
            merchant_url=merchant_url,
            success_url=success_url,
            error_url=error_url,
            customer_name=customer_name,
            currency=payment.currency
        )
        
        # Update payment with form data and callback URLs
        payment.provider_response = form_data
        payment.success_url = success_url
        payment.cancel_url = error_url
        payment.status = Payment.Status.PROCESSING
        payment.save()
        
        # Create CaixaBank form creation transaction
        PaymentTransaction.objects.create(
            payment=payment,
            action=PaymentTransaction.Action.CREATED,
            amount=payment.amount,
            provider_response=form_data,
            success=True,
            notes="CaixaBank payment form created successfully"
        )
        
        logger.info(f"CaixaBank payment created: {payment.payment_id}")
        
        return Response({
            'payment_id': payment.payment_id,
            'status': payment.status,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'provider': 'CaixaBank',
            'form_data': form_data,
            'message': 'CaixaBank payment form created successfully',
            'next_action': 'submit_form_to_gateway'
        }, status=status.HTTP_201_CREATED)
        
    except CaixaError as e:
        logger.error(f"CaixaBank payment creation error: {e}")
        
        # Update payment status
        payment.status = Payment.Status.FAILED
        payment.failure_reason = str(e)
        payment.save()
        
        # Create failed transaction
        PaymentTransaction.objects.create(
            payment=payment,
            action=PaymentTransaction.Action.FAILED,
            success=False,
            error_message=str(e),
            notes="CaixaBank payment form creation failed"
        )
        
        # CaixaBank creation failed - this will trigger cart reversion in calling function
        raise CaixaError(f'CaixaBank payment creation failed: {e}')


@extend_schema(
    summary="Get Payment Status",
    description="Get the current status and details of a payment",
    responses={
        200: PaymentDetailSerializer,
        404: {
            'description': 'Payment not found',
            'examples': {
                'application/json': {
                    'error': 'Payment not found'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_status(request, payment_id):
    """Get payment status and details."""
    try:
        payment = get_object_or_404(
            Payment, 
            payment_id=payment_id, 
            user=request.user
        )
        serializer = PaymentDetailSerializer(payment, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Get payment status error: {e}")
        return Response(
            {'error': 'Failed to retrieve payment status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="PayPal Payment Success",
    description="Handle PayPal payment success callback. PayPal redirects users here after successful payment approval.",
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='PayPal order ID (token)',
            required=True,
        ),
        OpenApiParameter(
            name='PayerID',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='PayPal payer ID',
            required=True,
        ),
    ],
    responses={
        200: {
            'description': 'Payment captured successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'Payment completed successfully',
                    'payment_id': 'PAY-20250916-ABC123456789'
                }
            }
        },
        400: {
            'description': 'Missing or invalid parameters',
            'examples': {
                'application/json': {
                    'success': False,
                    'error': 'Missing PayPal token or PayerID'
                }
            }
        },
        404: {
            'description': 'Payment not found',
            'examples': {
                'application/json': {
                    'success': False,
                    'error': 'Payment not found'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['GET'])
@permission_classes([AllowAny])  # PayPal callback doesn't include auth
def paypal_success(request):
    """Handle PayPal payment success callback."""
    try:
        # Get PayPal parameters
        paypal_order_id = request.GET.get('token')
        payer_id = request.GET.get('PayerID')
        
        if not paypal_order_id or not payer_id:
            return Response({
                'success': False,
                'error': 'Missing PayPal token or PayerID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"PayPal success callback: order_id={paypal_order_id}, payer_id={payer_id}")
        
        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(provider_transaction_id=paypal_order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PayPal order: {paypal_order_id}")
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if payment is already completed
        if payment.status == Payment.Status.COMPLETED:
            return Response({
                'success': True,
                'message': 'Payment already completed',
                'payment_id': payment.payment_id
            })
        
        with transaction.atomic():
            # Capture the payment on PayPal
            try:
                capture_response = capture_order(paypal_order_id)
                logger.info(f"PayPal capture response: {capture_response}")
                
                # Update payment status
                payment.status = Payment.Status.COMPLETED
                payment.processed_at = timezone.now()
                payment.provider_response = {
                    **payment.provider_response,
                    'capture_response': capture_response,
                    'payer_id': payer_id
                }
                payment.save()
                
                # Create transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.CAPTURED,
                    amount=payment.amount,
                    provider_transaction_id=paypal_order_id,
                    provider_response=capture_response,
                    success=True,
                    notes=f"PayPal payment captured successfully for payer {payer_id}"
                )
                
                # Update order payment status
                order = payment.order
                order.payment_status = order.PaymentStatus.PAID
                if order.status == order.Status.PENDING:
                    order.status = order.Status.CONFIRMED
                    order.confirmed_at = timezone.now()
                order.save()
                
                logger.info(f"Payment {payment.payment_id} completed successfully")
                
                return Response({
                    'success': True,
                    'message': 'Payment completed successfully',
                    'payment_id': payment.payment_id,
                    'order_number': order.order_number,
                    'amount': str(payment.amount),
                    'currency': payment.currency
                })
                
            except PayPalError as e:
                logger.error(f"PayPal capture error: {e}")
                
                # Update payment status to failed
                payment.status = Payment.Status.FAILED
                payment.failure_reason = str(e)
                payment.save()
                
                # Create failed transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.FAILED,
                    provider_transaction_id=paypal_order_id,
                    success=False,
                    error_message=str(e),
                    notes="PayPal capture failed"
                )
                
                return Response({
                    'success': False,
                    'error': f'Payment capture failed: {e}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"PayPal success callback error: {e}")
        return Response({
            'success': False,
            'error': 'Payment processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="PayPal Payment Cancel",
    description="Handle PayPal payment cancellation callback. PayPal redirects users here when they cancel the payment.",
    parameters=[
        OpenApiParameter(
            name='token',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='PayPal order ID (token)',
            required=True,
        ),
    ],
    responses={
        200: {
            'description': 'Payment cancellation handled',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'Payment cancelled successfully',
                    'payment_id': 'PAY-20250916-ABC123456789'
                }
            }
        },
        400: {
            'description': 'Missing token parameter',
            'examples': {
                'application/json': {
                    'success': False,
                    'error': 'Missing PayPal token'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['GET'])
@permission_classes([AllowAny])  # PayPal callback doesn't include auth
def paypal_cancel(request):
    """Handle PayPal payment cancellation callback."""
    try:
        # Get PayPal order ID
        paypal_order_id = request.GET.get('token')
        
        if not paypal_order_id:
            return Response({
                'success': False,
                'error': 'Missing PayPal token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"PayPal cancel callback: order_id={paypal_order_id}")
        
        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(provider_transaction_id=paypal_order_id)
            
            with transaction.atomic():
                # Update payment status
                payment.status = Payment.Status.CANCELLED
                payment.failure_reason = "User cancelled payment on PayPal"
                payment.save()
                
                # Create cancelled transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.CANCELLED,
                    provider_transaction_id=paypal_order_id,
                    success=True,
                    notes="Payment cancelled by user on PayPal"
                )
                
                # Revert cart to ACTIVE so user can try again
                from apps.cart.models import Cart
                try:
                    cart = Cart.objects.get(
                        user=payment.user, 
                        status=Cart.Status.CONVERTED
                    )
                    cart.status = Cart.Status.ACTIVE
                    cart.save()
                    logger.info(f"Cart reverted to ACTIVE for user {payment.user.id}")
                except Cart.DoesNotExist:
                    logger.warning(f"No converted cart found for user {payment.user.id}")
                
                # Optionally delete the order since payment was cancelled
                order = payment.order
                order.delete()
                logger.info(f"Order {order.order_number} deleted due to payment cancellation")
                
                logger.info(f"Payment {payment.payment_id} cancelled by user")
                
                return Response({
                    'success': True,
                    'message': 'Payment cancelled successfully, cart restored for retry',
                    'payment_id': payment.payment_id
                })
                
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for cancelled PayPal order: {paypal_order_id}")
            return Response({
                'success': True,
                'message': 'Payment cancellation noted'
            })
        
    except Exception as e:
        logger.error(f"PayPal cancel callback error: {e}")
        return Response({
            'success': False,
            'error': 'Payment cancellation processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="PayPal Webhook Handler",
    description="Handle PayPal webhook events for payment notifications",
    request={
        'application/json': {
            'type': 'object',
            'description': 'PayPal webhook event payload'
        }
    },
    responses={
        200: {
            'description': 'Webhook processed successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'Webhook processed successfully'
                }
            }
        },
        400: {
            'description': 'Invalid webhook or verification failed',
            'examples': {
                'application/json': {
                    'success': False,
                    'error': 'Webhook verification failed'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['POST'])
@permission_classes([AllowAny])  # PayPal webhook doesn't include auth
def paypal_webhook(request):
    """Handle PayPal webhook events."""
    try:
        # TODO: Implement webhook processing
        body = request.data
        headers = {k.upper(): v for k, v in request.headers.items()}
        # 1. Verify webhook signature using verify_webhook()
        try:
            ok = verify_webhook(headers, body)
        except Exception:
            return Response({"detail": "Verification failure"}, status=status.HTTP_400_BAD_REQUEST)
        if not ok:
            return Response({"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Process different event types
        event_type = body.get('event_type')
        logger.info(f"PayPal webhook received: {event_type}")
        
        # Get PayPal method for webhook storage
        paypal_method = get_object_or_404(PaymentMethod, provider=PaymentMethod.Provider.PAYPAL)
        
        # Store webhook event
        webhook_record = PaymentWebhook.objects.create(
            payment_method=paypal_method,
            event_type=event_type,
            event_id=body.get('id', ''),
            payload=body,
            headers=headers
        )
        
        # 3. Process specific event types
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            _handle_payment_capture_completed(body, webhook_record)
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            _handle_payment_capture_denied(body, webhook_record)
        elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
            _handle_payment_capture_refunded(body, webhook_record)
        elif event_type == 'CHECKOUT.ORDER.APPROVED':
            _handle_checkout_order_approved(body, webhook_record)
        else:
            logger.info(f"Unhandled PayPal webhook event: {event_type}")
        
        # Mark webhook as processed
        webhook_record.processed = True
        webhook_record.processed_at = timezone.now()
        webhook_record.save()
        
        return Response({
            'success': True,
            'message': f'Webhook {event_type} processed successfully'
        })
        
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        return Response({
            'success': False,
            'error': 'Webhook processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _handle_payment_capture_completed(body, webhook_record):
    """Handle PAYMENT.CAPTURE.COMPLETED webhook event."""
    try:
        # Extract PayPal order ID from webhook payload
        resource = body.get('resource', {})
        supplementary_data = resource.get('supplementary_data', {})
        related_ids = supplementary_data.get('related_ids', {})
        order_id = related_ids.get('order_id')
        
        if not order_id:
            logger.error("No order_id found in PAYMENT.CAPTURE.COMPLETED webhook")
            return
        
        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(provider_transaction_id=order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PayPal order: {order_id}")
            return
        
        # Link webhook to payment
        webhook_record.payment = payment
        webhook_record.save()
        
        # Only update if not already completed (idempotency)
        if payment.status != Payment.Status.COMPLETED:
            with transaction.atomic():
                # Update payment status
                payment.status = Payment.Status.COMPLETED
                payment.processed_at = timezone.now()
                payment.provider_response = {
                    **payment.provider_response,
                    'capture_webhook': body
                }
                payment.save()
                
                # Create transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.CAPTURED,
                    amount=payment.amount,
                    provider_transaction_id=order_id,
                    provider_response=body,
                    success=True,
                    notes="Payment captured via webhook"
                )
                
                # Update order status
                order = payment.order
                order.payment_status = order.PaymentStatus.PAID
                if order.status == order.Status.PENDING:
                    order.status = order.Status.CONFIRMED
                    order.confirmed_at = timezone.now()
                order.save()
                
                logger.info(f"Payment {payment.payment_id} completed via webhook")
        
    except Exception as e:
        logger.error(f"Error handling PAYMENT.CAPTURE.COMPLETED webhook: {e}")
        webhook_record.error_message = str(e)
        webhook_record.save()


def _handle_payment_capture_denied(body, webhook_record):
    """Handle PAYMENT.CAPTURE.DENIED webhook event."""
    try:
        # Extract PayPal order ID from webhook payload
        resource = body.get('resource', {})
        supplementary_data = resource.get('supplementary_data', {})
        related_ids = supplementary_data.get('related_ids', {})
        order_id = related_ids.get('order_id')
        
        if not order_id:
            logger.error("No order_id found in PAYMENT.CAPTURE.DENIED webhook")
            return
        
        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(provider_transaction_id=order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PayPal order: {order_id}")
            return
        
        # Link webhook to payment
        webhook_record.payment = payment
        webhook_record.save()
        
        with transaction.atomic():
            # Update payment status to failed
            payment.status = Payment.Status.FAILED
            payment.failure_reason = f"Payment capture denied: {resource.get('reason_code', 'Unknown')}"
            payment.provider_response = {
                **payment.provider_response,
                'denied_webhook': body
            }
            payment.save()
            
            # Create failed transaction record
            PaymentTransaction.objects.create(
                payment=payment,
                action=PaymentTransaction.Action.FAILED,
                provider_transaction_id=order_id,
                provider_response=body,
                success=False,
                error_message=payment.failure_reason,
                notes="Payment capture denied via webhook"
            )
            
            # Revert cart to ACTIVE so user can try again
            from apps.cart.models import Cart
            try:
                cart = Cart.objects.get(
                    user=payment.user, 
                    status=Cart.Status.CONVERTED
                )
                cart.status = Cart.Status.ACTIVE
                cart.save()
                logger.info(f"Cart reverted to ACTIVE for user {payment.user.id}")
            except Cart.DoesNotExist:
                logger.warning(f"No converted cart found for user {payment.user.id}")
            
            logger.info(f"Payment {payment.payment_id} denied via webhook")
        
    except Exception as e:
        logger.error(f"Error handling PAYMENT.CAPTURE.DENIED webhook: {e}")
        webhook_record.error_message = str(e)
        webhook_record.save()


def _handle_payment_capture_refunded(body, webhook_record):
    """Handle PAYMENT.CAPTURE.REFUNDED webhook event."""
    try:
        # Extract PayPal order ID from webhook payload
        resource = body.get('resource', {})
        supplementary_data = resource.get('supplementary_data', {})
        related_ids = supplementary_data.get('related_ids', {})
        order_id = related_ids.get('order_id')
        
        if not order_id:
            logger.error("No order_id found in PAYMENT.CAPTURE.REFUNDED webhook")
            return
        
        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(provider_transaction_id=order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PayPal order: {order_id}")
            return
        
        # Link webhook to payment
        webhook_record.payment = payment
        webhook_record.save()
        
        with transaction.atomic():
            # Check refund amount
            refund_amount = float(resource.get('amount', {}).get('value', 0))
            
            # Update payment status
            if refund_amount >= float(payment.amount):
                payment.status = Payment.Status.REFUNDED
            else:
                payment.status = Payment.Status.PARTIALLY_REFUNDED
            
            payment.provider_response = {
                **payment.provider_response,
                'refund_webhook': body
            }
            payment.save()
            
            # Create refund transaction record
            PaymentTransaction.objects.create(
                payment=payment,
                action=PaymentTransaction.Action.REFUNDED,
                amount=refund_amount,
                provider_transaction_id=order_id,
                provider_response=body,
                success=True,
                notes=f"Refund of ${refund_amount} processed via webhook"
            )
            
            logger.info(f"Payment {payment.payment_id} refunded (${refund_amount}) via webhook")
        
    except Exception as e:
        logger.error(f"Error handling PAYMENT.CAPTURE.REFUNDED webhook: {e}")
        webhook_record.error_message = str(e)
        webhook_record.save()


def _handle_checkout_order_approved(body, webhook_record):
    """Handle CHECKOUT.ORDER.APPROVED webhook event."""
    try:
        # Extract PayPal order ID from webhook payload
        resource = body.get('resource', {})
        order_id = resource.get('id')
        
        if not order_id:
            logger.error("No order_id found in CHECKOUT.ORDER.APPROVED webhook")
            return
        
        # Find payment by PayPal order ID
        try:
            payment = Payment.objects.get(provider_transaction_id=order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PayPal order: {order_id}")
            return
        
        # Link webhook to payment
        webhook_record.payment = payment
        webhook_record.save()
        
        # Only update if still processing (idempotency)
        if payment.status == Payment.Status.PROCESSING:
            with transaction.atomic():
                # Update payment with approval info
                payment.provider_response = {
                    **payment.provider_response,
                    'approval_webhook': body
                }
                payment.save()
                
                # Create authorization transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.AUTHORIZED,
                    amount=payment.amount,
                    provider_transaction_id=order_id,
                    provider_response=body,
                    success=True,
                    notes="Order approved via webhook"
                )
                
                logger.info(f"Payment {payment.payment_id} approved via webhook")
        
    except Exception as e:
        logger.error(f"Error handling CHECKOUT.ORDER.APPROVED webhook: {e}")
        webhook_record.error_message = str(e)
        webhook_record.save()


@extend_schema(
    summary="PayPal Webhook Test Handler (Development Only)",
    description="Test webhook processing without signature verification - for development testing only",
    request={
        'application/json': {
            'type': 'object',
            'description': 'PayPal webhook event payload'
        }
    },
    responses={
        200: {
            'description': 'Webhook processed successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'Test webhook processed successfully'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def paypal_webhook_test(request):
    """Test webhook handler without verification - for development only."""
    try:
        body = request.data
        event_type = body.get('event_type')
        logger.info(f"PayPal TEST webhook received: {event_type}")
        
        # Get PayPal method for webhook storage
        paypal_method = get_object_or_404(PaymentMethod, provider=PaymentMethod.Provider.PAYPAL)
        
        # Store webhook event
        webhook_record = PaymentWebhook.objects.create(
            payment_method=paypal_method,
            event_type=event_type,
            event_id=body.get('id', ''),
            payload=body,
            headers={'test': 'true'}
        )
        
        # Process specific event types (same logic as main webhook)
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            _handle_payment_capture_completed(body, webhook_record)
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            _handle_payment_capture_denied(body, webhook_record)
        elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
            _handle_payment_capture_refunded(body, webhook_record)
        elif event_type == 'CHECKOUT.ORDER.APPROVED':
            _handle_checkout_order_approved(body, webhook_record)
        else:
            logger.info(f"Unhandled PayPal test webhook event: {event_type}")
        
        # Mark webhook as processed
        webhook_record.processed = True
        webhook_record.processed_at = timezone.now()
        webhook_record.save()
        
        return Response({
            'success': True,
            'message': f'Test webhook {event_type} processed successfully',
            'webhook_id': webhook_record.id
        })
        
    except Exception as e:
        logger.error(f"PayPal test webhook error: {e}")
        return Response({
            'success': False,
            'error': f'Test webhook processing failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="CaixaBank Webhook Handler",
    description="Handle CaixaBank/Redsys webhook notifications for payment status",
    request={
        'application/x-www-form-urlencoded': {
            'type': 'object',
            'properties': {
                'Ds_SignatureVersion': {'type': 'string'},
                'Ds_MerchantParameters': {'type': 'string'},
                'Ds_Signature': {'type': 'string'}
            }
        }
    },
    responses={
        200: {
            'description': 'Webhook processed successfully',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'Payment processed successfully'
                }
            }
        },
        400: {
            'description': 'Invalid webhook or verification failed',
            'examples': {
                'application/json': {
                    'success': False,
                    'error': 'Invalid signature'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['POST'])
@permission_classes([AllowAny])  # CaixaBank webhook doesn't include auth
def caixa_webhook(request):
    """Handle CaixaBank/Redsys webhook notifications."""
    try:
        # Extract form data from webhook
        form_data = {
            'Ds_SignatureVersion': request.data.get('Ds_SignatureVersion'),
            'Ds_MerchantParameters': request.data.get('Ds_MerchantParameters'),
            'Ds_Signature': request.data.get('Ds_Signature')
        }
        
        logger.info(f"CaixaBank webhook received: {form_data}")
        
        # Process webhook response
        try:
            payment_data = process_webhook_response(form_data)
        except CaixaError as e:
            logger.error(f"CaixaBank webhook verification failed: {e}")
            return Response({
                'success': False,
                'error': 'Webhook verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get CaixaBank method for webhook storage
        caixa_method = get_object_or_404(PaymentMethod, provider=PaymentMethod.Provider.CAIXA)
        
        # Store webhook event
        webhook_record = PaymentWebhook.objects.create(
            payment_method=caixa_method,
            event_type='PAYMENT_NOTIFICATION',
            event_id=payment_data.get('authorization_code', ''),
            payload=payment_data,
            headers=dict(request.headers)
        )
        
        # Find payment by order number
        order_number = payment_data.get('order_number')
        if not order_number:
            logger.error("No order number found in CaixaBank webhook")
            return Response({
                'success': False,
                'error': 'Missing order number'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.orders.models import Order
            order = Order.objects.get(order_number=order_number)
            payment = Payment.objects.get(order=order)
        except (Order.DoesNotExist, Payment.DoesNotExist):
            logger.error(f"Payment not found for order: {order_number}")
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Link webhook to payment
        webhook_record.payment = payment
        webhook_record.save()
        
        with transaction.atomic():
            if payment_data['is_successful']:
                # Payment successful
                payment.status = Payment.Status.COMPLETED
                payment.processed_at = timezone.now()
                payment.provider_transaction_id = payment_data.get('authorization_code', '')
                payment.provider_response = {
                    **payment.provider_response,
                    'webhook_response': payment_data
                }
                payment.save()
                
                # Create successful transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.CAPTURED,
                    amount=payment_data['amount'],
                    provider_transaction_id=payment_data.get('authorization_code', ''),
                    provider_response=payment_data,
                    success=True,
                    notes=f"CaixaBank payment completed via webhook (Response: {payment_data['response_code']})"
                )
                
                # Update order status
                order.payment_status = order.PaymentStatus.PAID
                if order.status == order.Status.PENDING:
                    order.status = order.Status.CONFIRMED
                    order.confirmed_at = timezone.now()
                order.save()
                
                logger.info(f"CaixaBank payment {payment.payment_id} completed via webhook")
                
            else:
                # Payment failed
                payment.status = Payment.Status.FAILED
                payment.failure_reason = f"CaixaBank payment failed: Response code {payment_data['response_code']}"
                payment.provider_response = {
                    **payment.provider_response,
                    'webhook_response': payment_data
                }
                payment.save()
                
                # Create failed transaction record
                PaymentTransaction.objects.create(
                    payment=payment,
                    action=PaymentTransaction.Action.FAILED,
                    provider_response=payment_data,
                    success=False,
                    error_message=payment.failure_reason,
                    notes=f"CaixaBank payment failed via webhook (Response: {payment_data['response_code']})"
                )
                
                # Revert cart to ACTIVE so user can try again
                from apps.cart.models import Cart
                try:
                    cart = Cart.objects.get(
                        user=payment.user, 
                        status=Cart.Status.CONVERTED
                    )
                    cart.status = Cart.Status.ACTIVE
                    cart.save()
                    logger.info(f"Cart reverted to ACTIVE for user {payment.user.id}")
                except Cart.DoesNotExist:
                    logger.warning(f"No converted cart found for user {payment.user.id}")
                
                logger.info(f"CaixaBank payment {payment.payment_id} failed via webhook")
        
        # Mark webhook as processed
        webhook_record.processed = True
        webhook_record.processed_at = timezone.now()
        webhook_record.save()
        
        return Response({
            'success': True,
            'message': 'Payment processed successfully' if payment_data['is_successful'] else 'Payment failure processed'
        })
        
    except Exception as e:
        logger.error(f"CaixaBank webhook error: {e}")
        return Response({
            'success': False,
            'error': 'Webhook processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="CaixaBank Payment Success",
    description="Handle CaixaBank payment success callback. Users are redirected here after successful payment.",
    responses={
        200: {
            'description': 'Payment success handled',
            'examples': {
                'application/json': {
                    'success': True,
                    'message': 'Payment completed successfully'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # CaixaBank callback doesn't include auth
def caixa_success(request):
    """Handle CaixaBank payment success callback."""
    try:
        logger.info(f"CaixaBank success callback received: {request.data}")
        
        return Response({
            'success': True,
            'message': 'Payment completed successfully',
            'note': 'Payment status will be updated via webhook notification'
        })
        
    except Exception as e:
        logger.error(f"CaixaBank success callback error: {e}")
        return Response({
            'success': False,
            'error': 'Payment success processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="CaixaBank Payment Error",
    description="Handle CaixaBank payment error callback. Users are redirected here when payment fails.",
    responses={
        200: {
            'description': 'Payment error handled',
            'examples': {
                'application/json': {
                    'success': False,
                    'message': 'Payment failed'
                }
            }
        }
    },
    tags=['Payments']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # CaixaBank callback doesn't include auth
def caixa_error(request):
    """Handle CaixaBank payment error callback."""
    try:
        logger.info(f"CaixaBank error callback received: {request.data}")
        
        return Response({
            'success': False,
            'message': 'Payment failed',
            'note': 'Payment status will be updated via webhook notification'
        })
        
    except Exception as e:
        logger.error(f"CaixaBank error callback error: {e}")
        return Response({
            'success': False,
            'error': 'Payment error processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
