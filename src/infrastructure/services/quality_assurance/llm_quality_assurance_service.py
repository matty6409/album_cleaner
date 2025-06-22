"""
LLM-powered Quality Assurance Service implementation.
"""
import json
import yaml
import re
from typing import Dict, List, Optional
from pathlib import Path
from jinja2 import Template

from application.interfaces.services.quality_assurance_service_interface import QualityAssuranceService
from application.interfaces.services.llm_service_interface import LLMService
from domain.values_objects.language import Language
from infrastructure.logging.logger import logger

class LLMQualityAssuranceService(QualityAssuranceService):
    """
    LLM-powered quality assurance service for album cleaning results.
    """
    
    def __init__(self, llm_service: LLMService, prompts_dir: str = "src/prompts"):
        self.llm_service = llm_service
        self.prompts_dir = Path(prompts_dir)
        self._load_prompts()
    
    def _load_prompts(self):
        """Load quality assurance prompts from YAML file."""
        try:
            with open(self.prompts_dir / "quality_assurance_prompt.yaml", 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load quality assurance prompts: {e}")
            raise
    
    def _extract_json_from_response(self, response: str) -> dict:
        """Extract JSON from LLM response, handling cases where extra text is included."""
        try:
            # First try to parse the entire response as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # Look for JSON object in the response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError("No JSON object found in response")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to extract JSON from response: {e}")
                logger.debug(f"Response was: {response}")
                raise
    
    def _extract_json_array_from_response(self, response: str) -> list:
        """Extract JSON array from LLM response, handling cases where extra text is included."""
        try:
            # First try to parse the entire response as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # Look for JSON array in the response
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError("No JSON array found in response")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to extract JSON array from response: {e}")
                logger.debug(f"Response was: {response}")
                raise
    
    def review_mapping_quality(
        self,
        artist_name: str,
        album_name: str,
        local_files: List[str],
        proposed_mapping: Dict[str, str],
        official_tracks: List[str],
        target_language: Language
    ) -> Dict[str, any]:
        """
        Review the quality of a proposed filename mapping using LLM.
        """
        try:
            # Render prompts
            system_template = Template(self.prompts['quality_review']['system'])
            user_template = Template(self.prompts['quality_review']['user'])
            
            system_prompt = system_template.render()
            user_prompt = user_template.render(
                artist_name=artist_name,
                album_name=album_name,
                target_language=target_language.value,
                local_files=local_files,
                proposed_mapping=proposed_mapping,
                official_tracks=official_tracks if official_tracks else None
            )
            
            # Get LLM review
            response = self.llm_service.generate_response(system_prompt, user_prompt)
            
            # Parse JSON response with robust extraction
            review_result = self._extract_json_from_response(response)
            
            # Validate required fields
            required_fields = ['approved', 'issues', 'recommendations', 'confidence_score', 
                             'language_compliance', 'track_number_compliance']
            for field in required_fields:
                if field not in review_result:
                    logger.warning(f"QA response missing required field: {field}")
                    if field == 'approved':
                        review_result[field] = False
                    elif field in ['issues', 'recommendations']:
                        review_result[field] = []
                    elif field == 'confidence_score':
                        review_result[field] = 0.0
                    else:
                        review_result[field] = False
            
            logger.info(f"QA Review completed - Approved: {review_result.get('approved')}, "
                       f"Confidence: {review_result.get('confidence_score')}")
            
            return review_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse QA review response: {e}")
            return {
                "approved": False,
                "issues": [f"Failed to parse QA response: {e}"],
                "recommendations": ["Retry with different prompt"],
                "confidence_score": 0.0,
                "language_compliance": False,
                "track_number_compliance": False
            }
        except Exception as e:
            logger.error(f"QA review failed: {e}")
            return {
                "approved": False,
                "issues": [f"QA review error: {e}"],
                "recommendations": ["Manual review required"],
                "confidence_score": 0.0,
                "language_compliance": False,
                "track_number_compliance": False
            }
    
    def suggest_search_alternatives(
        self,
        artist_name: str,
        album_name: str,
        failed_searches: List[str],
        target_language: Language
    ) -> List[str]:
        """
        Suggest alternative search terms when initial Spotify searches fail.
        """
        try:
            # Render prompts
            system_template = Template(self.prompts['search_alternatives']['system'])
            user_template = Template(self.prompts['search_alternatives']['user'])
            
            system_prompt = system_template.render()
            user_prompt = user_template.render(
                artist_name=artist_name,
                album_name=album_name,
                target_language=target_language.value,
                failed_searches=failed_searches
            )
            
            # Get LLM suggestions
            response = self.llm_service.generate_response(system_prompt, user_prompt)
            
            # Parse JSON array response with robust extraction
            alternatives = self._extract_json_array_from_response(response)
            
            # Validate that we got a list of strings
            if not isinstance(alternatives, list):
                logger.warning("Search alternatives response is not a list")
                return []
            
            # Filter out non-string items
            alternatives = [alt for alt in alternatives if isinstance(alt, str)]
            
            logger.info(f"Generated {len(alternatives)} alternative search terms")
            return alternatives
            
        except Exception as e:
            logger.error(f"Failed to generate search alternatives: {e}")
            return []
