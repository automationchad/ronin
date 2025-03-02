"""Service for analyzing job postings using OpenAI."""

import json

from typing import Dict, List, Optional
from loguru import logger
from tasks.job_scraping.prompts import TECH_KEYWORDS_PROMPT


class TechKeywordsService:
    """Service for analyzing job postings using OpenAI."""

    def __init__(self, config: Dict, client):
        self.config = config
        self.client = client  # Store the OpenAI client
        self._system_prompt = TECH_KEYWORDS_PROMPT

    def analyze_job(self, job_data: Dict) -> Optional[Dict]:
        """
        Analyze a job posting using OpenAI.

        Args:
            job_data: Dictionary containing job information with a description field

        Returns:
            Dictionary containing the enriched job data with OpenAI analysis,
            or None if analysis fails
        """
        try:
            # Get job analysis from OpenAI using the client directly
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # or your preferred model
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {
                        "role": "user",
                        "content": f"Get the tech keywords from this job description:\n\n{job_data['description']}",
                    },
                ],
                temperature=0.7,
            )

            if not response:
                logger.error(
                    f"Failed to get analysis from OpenAI for job {job_data.get('job_id')}"
                )
                return None

            try:
                # Extract and clean the content from the response
                content = response.choices[0].message.content

                # Remove markdown code block if present
                content = content.replace("```json\n", "").replace("\n```", "").strip()

                # Parse the JSON
                analysis_data = json.loads(content)

                if not analysis_data:
                    logger.error(
                        f"No valid keywords data in OpenAI response for job {job_data.get('job_id')}"
                    )
                    return None

                # Validate required fields
                if "tech_keywords" not in analysis_data:
                    logger.error("Missing tech_keywords field in analysis data")
                    return None

                # Ensure tech_keywords is a list
                if not isinstance(analysis_data["tech_keywords"], list):
                    logger.error("tech_keywords must be a list")
                    return None

                return {**job_data, "analysis": analysis_data}

            except Exception as e:
                logger.error(
                    f"Failed to process OpenAI response for job {job_data.get('job_id')}: {str(e)}"
                )
                logger.error(f"Raw response: {response}")
                return None

        except Exception as e:
            logger.error(
                f"Error analyzing job {job_data.get('title', 'Unknown')} (ID: {job_data.get('job_id', 'Unknown')}): {str(e)}"
            )
            logger.exception("Full traceback:")
            return None
