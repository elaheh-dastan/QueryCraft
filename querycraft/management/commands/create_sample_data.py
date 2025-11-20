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
        today = date.today()

        # Calculate last month date range
        # Last month means the previous calendar month
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)

        # Split customers into different time periods
        # 30% from last month (to answer the query)
        # 20% from this month
        # 50% from older periods
        num_last_month = int(num_customers * 0.3)
        num_this_month = int(num_customers * 0.2)
        num_older = num_customers - num_last_month - num_this_month

        customer_count = 0

        # Create customers from last month
        for i in range(num_last_month):
            # Random date within last month
            days_in_last_month = (last_day_last_month - first_day_last_month).days + 1
            random_day = random.randint(0, days_in_last_month - 1)
            registration_date = first_day_last_month + timedelta(days=random_day)

            customer = Customer.objects.create(
                name=f"Customer {customer_count + 1}",
                email=f"customer{customer_count + 1}@example.com",
                registration_date=registration_date,
            )
            customers.append(customer)
            customer_count += 1

        # Create customers from this month
        for i in range(num_this_month):
            # Random date from this month up to today
            days_in_current_month = (today - first_day_current_month).days
            if days_in_current_month > 0:
                random_day = random.randint(0, days_in_current_month)
                registration_date = first_day_current_month + timedelta(days=random_day)
            else:
                registration_date = today

            customer = Customer.objects.create(
                name=f"Customer {customer_count + 1}",
                email=f"customer{customer_count + 1}@example.com",
                registration_date=registration_date,
            )
            customers.append(customer)
            customer_count += 1

        # Create customers from older periods (2-12 months ago)
        for i in range(num_older):
            # Random date from 60 to 365 days ago (older than last month)
            days_ago = random.randint(60, 365)
            registration_date = today - timedelta(days=days_ago)

            customer = Customer.objects.create(
                name=f"Customer {customer_count + 1}",
                email=f"customer{customer_count + 1}@example.com",
                registration_date=registration_date,
            )
            customers.append(customer)
            customer_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ {num_customers} customers created"))
        self.stdout.write(
            self.style.SUCCESS(
                f"  - {num_last_month} registered last month ({first_day_last_month} to {last_day_last_month})"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"  - {num_this_month} registered this month"))
        self.stdout.write(self.style.SUCCESS(f"  - {num_older} registered in older periods"))

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
