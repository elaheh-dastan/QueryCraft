"""
Management command to process PDF resumes from a directory
"""

import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from querycraft.services.profile_extractor import ProfileExtractor
from querycraft.services.resume_parser import ResumeParser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process PDF resumes from a directory and extract profile information"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "directory",
            type=str,
            help="Directory path containing PDF resume files",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Extract and display information without saving to database",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip resumes if a profile with the same name already exists",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        directory_path = Path(options["directory"])
        dry_run = options["dry_run"]
        skip_existing = options["skip_existing"]

        self.stdout.write("=" * 80)
        self.stdout.write("Processing PDF Resumes")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Directory: {directory_path}")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write(f"Skip existing: {skip_existing}")
        self.stdout.write("")

        # Validate directory
        if not directory_path.exists():
            self.stdout.write(
                self.style.ERROR(f"✗ Directory not found: {directory_path}")
            )
            return

        if not directory_path.is_dir():
            self.stdout.write(
                self.style.ERROR(f"✗ Path is not a directory: {directory_path}")
            )
            return

        # Parse PDFs
        self.stdout.write("Step 1: Extracting text from PDF files...")
        try:
            pdf_texts = ResumeParser.extract_text_from_directory(directory_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error parsing PDFs: {e}"))
            return

        if not pdf_texts:
            self.stdout.write(self.style.WARNING("⚠ No PDF files found in directory"))
            return

        self.stdout.write(self.style.SUCCESS(f"✓ Found {len(pdf_texts)} PDF file(s)"))
        self.stdout.write("")

        # Extract profiles
        self.stdout.write("Step 2: Extracting profile information using LLM...")
        extractor = ProfileExtractor()

        success_count = 0
        error_count = 0
        skipped_count = 0

        for pdf_filename, resume_text in pdf_texts.items():
            if not resume_text:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Skipping {pdf_filename} (no text extracted)")
                )
                error_count += 1
                continue

            self.stdout.write(f"Processing: {pdf_filename}")

            try:
                # Extract profile data
                profile_data = extractor.extract_profile(resume_text)

                # Check if profile already exists
                if skip_existing:
                    from querycraft.models import Profile

                    existing = Profile.objects.filter(name=profile_data.name).first()
                    if existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Skipping - Profile with name '{profile_data.name}' already exists (ID: {existing.id})"
                            )
                        )
                        skipped_count += 1
                        continue

                if dry_run:
                    # Display extracted information
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Extracted profile: {profile_data.name}"
                        )
                    )
                    self.stdout.write(f"    Name: {profile_data.name}")
                    self.stdout.write(f"    Cellphone: {profile_data.cellphone}")
                    self.stdout.write(f"    Education: {profile_data.education}")
                    self.stdout.write(
                        f"    Skills ({len(profile_data.skills)}): {', '.join(profile_data.skills[:5])}{'...' if len(profile_data.skills) > 5 else ''}"
                    )
                    self.stdout.write(
                        f"    Companies ({len(profile_data.companies)}): {', '.join(profile_data.companies[:5])}{'...' if len(profile_data.companies) > 5 else ''}"
                    )
                    success_count += 1
                else:
                    # Create profile in database
                    profile = extractor.create_profile_from_text(resume_text)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Created Profile: {profile.name} (ID: {profile.id})"
                        )
                    )
                    success_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error processing {pdf_filename}: {e}")
                )
                logger.error(f"Error processing {pdf_filename}: {e}", exc_info=True)
                error_count += 1

            self.stdout.write("")

        # Summary
        self.stdout.write("=" * 80)
        self.stdout.write("Summary")
        self.stdout.write("=" * 80)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully processed: {success_count}")
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠ Skipped (existing): {skipped_count}")
            )
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
        self.stdout.write("=" * 80)
