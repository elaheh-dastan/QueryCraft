import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from querycraft.models import Customer, Order, Product


class Command(BaseCommand):
    help = "Create sample data for testing the application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--customers",
            type=int,
            default=20,
            help="Number of sample customers",
        )
        parser.add_argument(
            "--products",
            type=int,
            default=15,
            help="Number of sample products",
        )
        parser.add_argument(
            "--orders",
            type=int,
            default=50,
            help="Number of sample orders",
        )

    def handle(self, *args, **options):
        num_customers = options["customers"]
        num_products = options["products"]
        num_orders = options["orders"]

        self.stdout.write("Creating sample data...")

        # Delete previous data (optional)
        Order.objects.all().delete()
        Customer.objects.all().delete()
        Product.objects.all().delete()

        # Create products first
        categories = ["Electronics", "Clothing", "Books", "Food", "Toys", "Home & Garden"]
        products = []
        for i in range(num_products):
            product = Product.objects.create(
                name=f"Product {i + 1}",
                category=random.choice(categories),
                price=round(random.uniform(10.0, 500.0), 2),
            )
            products.append(product)

        self.stdout.write(self.style.SUCCESS(f"✓ {num_products} products created"))

        # Create customers
        customers = []
        for i in range(num_customers):
            # Create customers at different time periods
            days_ago = random.randint(0, 365)
            registration_date = date.today() - timedelta(days=days_ago)

            customer = Customer.objects.create(
                name=f"Customer {i + 1}",
                email=f"customer{i + 1}@example.com",
                registration_date=registration_date,
            )
            customers.append(customer)

        self.stdout.write(self.style.SUCCESS(f"✓ {num_customers} customers created"))

        # Create orders
        statuses = ["pending", "completed", "completed", "cancelled"]
        for _ in range(num_orders):
            customer = random.choice(customers)
            product = random.choice(products)
            days_ago = random.randint(0, 90)
            order_date = date.today() - timedelta(days=days_ago)

            Order.objects.create(
                customer=customer,
                product=product,
                order_date=order_date,
                quantity=random.randint(1, 10),
                status=random.choice(statuses),
            )

        self.stdout.write(self.style.SUCCESS(f"✓ {num_orders} orders created"))
        self.stdout.write(self.style.SUCCESS("✓ Sample data created successfully!"))
