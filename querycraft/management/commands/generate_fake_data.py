import logging
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from faker import Faker

from querycraft.models import Customer, Order, Product

# Set up logger for this command
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate fake data using Faker library for Customer, Product, and Order models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--customers",
            type=int,
            default=50,
            help="Number of fake customers to generate (default: 50)",
        )
        parser.add_argument(
            "--products",
            type=int,
            default=30,
            help="Number of fake products to generate (default: 30)",
        )
        parser.add_argument(
            "--orders",
            type=int,
            default=100,
            help="Number of fake orders to generate (default: 100)",
        )
        parser.add_argument(
            "--locale",
            type=str,
            default="en_US",
            help="Faker locale (default: en_US)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before generating new data",
        )

    def handle(self, *args, **options):
        num_customers = options["customers"]
        num_products = options["products"]
        num_orders = options["orders"]
        locale = options["locale"]
        clear_data = options["clear"]

        # Log command execution start
        logger.info("=" * 60)
        logger.info("Starting fake data generation command")
        logger.info(f"Parameters: customers={num_customers}, products={num_products}, orders={num_orders}")
        logger.info(f"Locale: {locale}, Clear existing data: {clear_data}")
        logger.info("=" * 60)

        # Initialize Faker with specified locale
        fake = Faker(locale)
        logger.info(f"Faker initialized with locale: {locale}")

        self.stdout.write(self.style.WARNING(f"Generating fake data with locale: {locale}"))

        # Clear existing data if requested
        if clear_data:
            self.stdout.write("Clearing existing data...")
            Order.objects.all().delete()
            Customer.objects.all().delete()
            Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared"))

        # Generate fake customers
        self.stdout.write(f"Generating {num_customers} customers...")
        customers = []
        for _ in range(num_customers):
            customer = Customer.objects.create(
                name=fake.name(),
                email=fake.unique.email(),
                registration_date=fake.date_between(start_date="-2y", end_date="today"),
            )
            customers.append(customer)

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully created {num_customers} customers")
        )

        # Generate fake products with realistic categories and names
        self.stdout.write(f"Generating {num_products} products...")
        categories = [
            "Electronics",
            "Clothing",
            "Books",
            "Food & Beverages",
            "Toys & Games",
            "Home & Garden",
            "Sports & Outdoors",
            "Health & Beauty",
            "Automotive",
            "Office Supplies",
        ]

        products = []
        for _ in range(num_products):
            category = random.choice(categories)
            # Generate product name based on category
            if category == "Electronics":
                product_name = f"{fake.company()} {random.choice(['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard'])}"
            elif category == "Clothing":
                product_name = f"{random.choice(['Cotton', 'Wool', 'Silk', 'Denim'])} {random.choice(['Shirt', 'Pants', 'Jacket', 'Dress'])}"
            elif category == "Books":
                product_name = fake.catch_phrase()
            elif category == "Food & Beverages":
                product_name = f"{fake.word().capitalize()} {random.choice(['Coffee', 'Tea', 'Juice', 'Snacks', 'Cereal'])}"
            else:
                product_name = f"{fake.word().capitalize()} {fake.word().capitalize()}"

            product = Product.objects.create(
                name=product_name[:200],  # Ensure it fits in the CharField
                category=category,
                price=round(fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=5, max_value=9999), 2),
            )
            products.append(product)

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully created {num_products} products")
        )

        # Generate fake orders
        self.stdout.write(f"Generating {num_orders} orders...")
        statuses = ["pending", "completed", "cancelled"]
        status_weights = [0.2, 0.7, 0.1]  # 20% pending, 70% completed, 10% cancelled

        for _ in range(num_orders):
            customer = random.choice(customers)
            product = random.choice(products)

            # Generate order date within the last year
            order_date = fake.date_between(start_date="-1y", end_date="today")

            # Ensure order date is after customer registration date
            if order_date < customer.registration_date:
                order_date = customer.registration_date + timedelta(days=random.randint(1, 30))

            Order.objects.create(
                customer=customer,
                product=product,
                order_date=order_date,
                quantity=random.randint(1, 10),
                status=random.choices(statuses, weights=status_weights)[0],
            )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully created {num_orders} orders")
        )

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("✓ Fake data generation completed!"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total customers: {Customer.objects.count()}")
        self.stdout.write(f"Total products: {Product.objects.count()}")
        self.stdout.write(f"Total orders: {Order.objects.count()}")
        self.stdout.write("=" * 50)
