from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from querycraft.models import Customer, Product, Order
from faker import Faker
import random

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with realistic data using Faker (at least 1000 rows)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customers',
            type=int,
            default=300,
            help='Number of customers to create (default: 300)',
        )
        parser.add_argument(
            '--products',
            type=int,
            default=100,
            help='Number of products to create (default: 100)',
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=1000,
            help='Number of orders to create (default: 1000)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        num_customers = options['customers']
        num_products = options['products']
        num_orders = options['orders']
        clear_existing = options['clear']

        total_rows = num_customers + num_products + num_orders
        
        if total_rows < 1000:
            self.stdout.write(
                self.style.WARNING(
                    f'Total rows ({total_rows}) is less than 1000. '
                    f'Adjusting orders to meet minimum requirement...'
                )
            )
            num_orders = 1000 - num_customers - num_products
            if num_orders < 1:
                num_orders = 1000
            total_rows = num_customers + num_products + num_orders

        self.stdout.write(f'Seeding database with {total_rows} rows...')
        self.stdout.write(f'  - Customers: {num_customers}')
        self.stdout.write(f'  - Products: {num_products}')
        self.stdout.write(f'  - Orders: {num_orders}')

        if clear_existing:
            self.stdout.write('Clearing existing data...')
            Order.objects.all().delete()
            Customer.objects.all().delete()
            Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Existing data cleared'))

        # Product categories
        categories = [
            'Electronics', 'Clothing', 'Books', 'Food & Beverages',
            'Toys & Games', 'Home & Garden', 'Sports & Outdoors',
            'Health & Beauty', 'Automotive', 'Office Supplies',
            'Furniture', 'Jewelry', 'Musical Instruments', 'Pet Supplies'
        ]

        # Order statuses with weighted distribution
        order_statuses = ['pending', 'completed', 'completed', 'completed', 'cancelled']

        with transaction.atomic():
            # Step 1: Create Products (no dependencies)
            self.stdout.write('Creating products...')
            products = []
            for i in range(num_products):
                product = Product(
                    name=fake.catch_phrase() + ' ' + fake.word().title(),
                    category=random.choice(categories),
                    price=round(random.uniform(5.0, 999.99), 2)
                )
                products.append(product)
            
            # Bulk create products
            Product.objects.bulk_create(products, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f'✓ {num_products} products created'))

            # Step 2: Create Customers (no dependencies)
            self.stdout.write('Creating customers...')
            customers = []
            # Generate registration dates over the past 2 years
            start_date = date.today() - timedelta(days=730)
            
            for i in range(num_customers):
                # Generate unique email
                email = fake.unique.email()
                # Generate registration date
                days_ago = random.randint(0, 730)
                registration_date = start_date + timedelta(days=days_ago)
                
                customer = Customer(
                    name=fake.name(),
                    email=email,
                    registration_date=registration_date
                )
                customers.append(customer)
            
            # Bulk create customers
            Customer.objects.bulk_create(customers, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f'✓ {num_customers} customers created'))

            # Step 3: Create Orders (depends on customers and products)
            self.stdout.write('Creating orders...')
            
            # Fetch all created customers and products for referential integrity
            all_customers = list(Customer.objects.all())
            all_products = list(Product.objects.all())
            
            if not all_customers or not all_products:
                self.stdout.write(
                    self.style.ERROR('Error: No customers or products available for orders')
                )
                return

            orders = []
            # Generate order dates over the past year
            order_start_date = date.today() - timedelta(days=365)
            
            for i in range(num_orders):
                # Select random customer and product (ensuring referential integrity)
                customer = random.choice(all_customers)
                product = random.choice(all_products)
                
                # Order date should be after customer registration date
                days_since_registration = (date.today() - customer.registration_date).days
                if days_since_registration > 0:
                    max_days_ago = min(365, days_since_registration)
                    days_ago = random.randint(0, max_days_ago)
                else:
                    days_ago = 0
                
                order_date = date.today() - timedelta(days=days_ago)
                
                order = Order(
                    customer=customer,
                    product=product,
                    order_date=order_date,
                    quantity=random.randint(1, 20),
                    status=random.choice(order_statuses)
                )
                orders.append(order)
            
            # Bulk create orders
            Order.objects.bulk_create(orders, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f'✓ {num_orders} orders created'))

        # Display summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Total Customers: {Customer.objects.count()}')
        self.stdout.write(f'Total Products: {Product.objects.count()}')
        self.stdout.write(f'Total Orders: {Order.objects.count()}')
        self.stdout.write(f'Total Rows: {Customer.objects.count() + Product.objects.count() + Order.objects.count()}')
        self.stdout.write('')

