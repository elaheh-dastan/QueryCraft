from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from querycraft.models import User, Order
import random


class Command(BaseCommand):
    help = 'Create sample data for testing the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of sample users',
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=50,
            help='Number of sample orders',
        )

    def handle(self, *args, **options):
        num_users = options['users']
        num_orders = options['orders']

        self.stdout.write('Creating sample data...')

        # Delete previous data (optional)
        User.objects.all().delete()
        Order.objects.all().delete()

        # Create users
        users = []
        for i in range(num_users):
            # Create users at different time periods
            days_ago = random.randint(0, 60)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            user = User.objects.create(
                username=f'user_{i+1}',
                email=f'user_{i+1}@example.com',
                created_at=created_at,
                is_active=random.choice([True, True, True, False])  # Most are active
            )
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'✓ {num_users} users created'))

        # Create orders
        for i in range(num_orders):
            user = random.choice(users)
            days_ago = random.randint(0, 30)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            Order.objects.create(
                user=user,
                total_amount=random.uniform(10.0, 1000.0),
                created_at=created_at,
                status=random.choice(['pending', 'completed', 'completed', 'cancelled'])
            )

        self.stdout.write(self.style.SUCCESS(f'✓ {num_orders} orders created'))
        self.stdout.write(self.style.SUCCESS('✓ Sample data created successfully!'))

