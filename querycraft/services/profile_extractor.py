"""
Service for extracting profile information from resume text using LLM
"""

import json
import logging
from typing import Any

from django.conf import settings
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field, field_validator

from querycraft.models import Profile

logger = logging.getLogger(__name__)


class ProfileData(BaseModel):
    """Structured profile data extracted from resume"""

    name: str = Field(description="Full name of the person")
    cellphone: str = Field(description="Phone number")
    skills: list[str] = Field(default_factory=list, description="List of skills")
    education: str = Field(description="Education level: bachelor, master, or phd")
    companies: list[str] = Field(default_factory=list, description="List of companies worked for")

    @field_validator("education")
    @classmethod
    def validate_education(cls, v: str) -> str:
        """Validate education level matches Profile model choices"""
        v_lower = v.lower().strip()
        valid_choices = ["bachelor", "master", "phd"]
        # Try to match common variations
        if "bachelor" in v_lower or "bachelor's" in v_lower or "bs" in v_lower or "ba" in v_lower:
            return "bachelor"
        elif "master" in v_lower or "master's" in v_lower or "ms" in v_lower or "ma" in v_lower or "mba" in v_lower:
            return "master"
        elif "phd" in v_lower or "ph.d" in v_lower or "doctorate" in v_lower or "doctoral" in v_lower:
            return "phd"
        elif v_lower in valid_choices:
            return v_lower
        else:
            logger.warning(f"Unknown education level '{v}', defaulting to 'bachelor'")
            return "bachelor"


class ProfileExtractor:
    """Service for extracting profile information from resume text using LLM"""

    def __init__(self) -> None:
        logger.info("Initializing ProfileExtractor")
        logger.debug(
            "Ollama configuration - Model: %s, Base URL: %s",
            settings.OLLAMA_MODEL_NAME,
            settings.OLLAMA_BASE_URL,
        )

        # Initialize LangChain Ollama LLM
        self.llm = OllamaLLM(
            model=settings.OLLAMA_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,  # Lower temperature for more consistent extraction
            num_predict=1024,  # More tokens for structured output
        )

        # Create prompt template for profile extraction
        self.prompt_template = PromptTemplate.from_template(
            """You are an expert at extracting structured information from resumes.
Resume text:
{resume_text}

Extract the profile information from the resume text above. Return a JSON object with the following structure:
{{
  "name": "Full Name",
}}

JSON:"""
        )

        logger.info("ProfileExtractor initialized successfully")

#     def get_profile_schema_info(self) -> str:
#         """Get Profile model schema information for the prompt"""
#         schema_info = """
# Profile table schema:
# - name (VARCHAR): Full name of the person
# - cellphone (VARCHAR): Phone number
# - skills (JSON array of strings): List of technical and professional skills
# - education (VARCHAR): Education level - must be one of: "bachelor", "master", or "phd"
# - companies (JSON array of strings): List of company names where the person has worked
# """
#         return schema_info

    def get_profile_schema_info(self) -> str:
        """Get Profile model schema information for the prompt"""
        schema_info = """
Profile table schema:
- name (VARCHAR): Full name of the person
"""
        return schema_info

    def extract_profile(self, resume_text: str) -> ProfileData:
        """
        Extract profile information from resume text using LLM

        Args:
            resume_text: Text content extracted from resume PDF

        Returns:
            ProfileData object with extracted information

        Raises:
            Exception: If extraction fails
        """
        logger.info("Extracting profile information from resume text")
        logger.debug(f"Resume text length: {len(resume_text)} characters")

        try:
            # Create prompt chain
            chain = self.prompt_template | self.llm
            logger.debug("Invoking Ollama LLM for profile extraction...")

            # Invoke the chain
            response = chain.invoke({"resume_text": resume_text})

            # Log response details
            logger.debug("Ollama response type: %s", type(response))
            response_text = response.strip() if isinstance(response, str) else str(response).strip()

            logger.debug("Raw LLM response (length=%d): '%s'", len(response_text), response_text[:200])

            # Parse JSON response
            # Try to extract JSON from markdown code blocks if present
            if "```" in response_text:
                # Extract content between code blocks
                import re

                match = re.search(r"```(?:json)?\s*\n?(.*?)```", response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    response_text = match.group(1).strip()

            # Parse JSON
            try:
                profile_dict = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response_text}")
                raise Exception(f"Failed to parse LLM response as JSON: {e}") from e

            # Validate and create ProfileData
            profile_data = ProfileData(**profile_dict)
            logger.info(f"Successfully extracted profile: {profile_data.name}")
            logger.debug(f"Profile data: {profile_data.model_dump()}")

            return profile_data

        except Exception as e:
            logger.error(f"Error extracting profile: {e}", exc_info=True)
            raise Exception(f"Profile extraction failed: {e}") from e

    def create_profile_from_text(self, resume_text: str) -> Profile:
        """
        Extract profile information and create a Profile model instance

        Args:
            resume_text: Text content extracted from resume PDF

        Returns:
            Profile model instance (saved to database)

        Raises:
            Exception: If extraction or creation fails
        """
        logger.info("Creating Profile from resume text")

        # Extract profile data
        profile_data = self.extract_profile(resume_text)

        # Create Profile instance
        profile = Profile.objects.create(
            name=profile_data.name,
            cellphone=profile_data.cellphone,
            skills=profile_data.skills,
            education=profile_data.education,
            companies=profile_data.companies,
        )

        logger.info(f"Successfully created Profile: {profile.name} (ID: {profile.id})")
        return profile

