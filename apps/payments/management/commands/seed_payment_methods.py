from django.core.management.base import BaseCommand
from apps.payments.models import PaymentMethod


class Command(BaseCommand):
    help = 'Seed payment methods data'

    def handle(self, *args, **options):
        payment_methods_data = [
            {
                'provider': PaymentMethod.Provider.PAYPAL,
                'display_name': 'PayPal',
                'is_active': True,
                'description': 'Pay with your PayPal account or credit/debit card',
                'sort_order': 1,
                'logo_url': 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/paypal/paypal-original.svg',
                'configuration': {
                    'supports_redirect': True,
                    'supports_webhooks': True,
                    'currencies': ['USD', 'EUR', 'GBP']
                }
            },
            {
                'provider': PaymentMethod.Provider.CAIXA,
                'display_name': 'Caixa',
                'is_active': False,  # Will be activated when implemented
                'description': 'Pay with Caixa banking services',
                'sort_order': 2,
                'logo_url': '',
                'configuration': {
                    'supports_redirect': True,
                    'supports_webhooks': False,
                    'currencies': ['EUR']
                }
            },
            {
                'provider': PaymentMethod.Provider.BIZUM,
                'display_name': 'Bizum',
                'is_active': False,  # Will be activated when implemented
                'description': 'Pay instantly with Bizum',
                'sort_order': 3,
                'logo_url': '',
                'configuration': {
                    'supports_redirect': False,
                    'supports_webhooks': False,
                    'currencies': ['EUR']
                }
            },
            {
                'provider': PaymentMethod.Provider.BINANCE_PAY,
                'display_name': 'Binance Pay',
                'is_active': False,  # Will be activated when implemented
                'description': 'Pay with cryptocurrency via Binance Pay',
                'sort_order': 4,
                'logo_url': '',
                'configuration': {
                    'supports_redirect': True,
                    'supports_webhooks': True,
                    'currencies': ['USDT', 'BUSD', 'BTC', 'ETH']
                }
            }
        ]

        created_count = 0
        updated_count = 0

        for method_data in payment_methods_data:
            payment_method, created = PaymentMethod.objects.get_or_create(
                provider=method_data['provider'],
                defaults=method_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created payment method: {payment_method.display_name}'
                    )
                )
            else:
                # Update existing payment method
                for key, value in method_data.items():
                    if key != 'provider':
                        setattr(payment_method, key, value)
                payment_method.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated payment method: {payment_method.display_name}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Payment methods seeded successfully! '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )