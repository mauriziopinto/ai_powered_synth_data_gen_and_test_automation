"""Data Processor Agent for identifying sensitive fields in production data."""

import re
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

from shared.models.sensitivity import FieldClassification, SensitivityReport
from shared.utils.confluence_client import ConfluenceClient
from shared.utils.explanation_generator import get_explanation_generator, Explanation


def map_pandas_dtype_to_friendly_name(dtype_str: str) -> str:
    """Map pandas dtype to user-friendly type name.
    
    Args:
        dtype_str: String representation of pandas dtype
        
    Returns:
        User-friendly type name: 'string', 'integer', 'float', 'boolean', 'date', 'datetime'
    """
    dtype_lower = dtype_str.lower()
    
    # Integer types
    if 'int' in dtype_lower:
        return 'integer'
    
    # Float types
    if 'float' in dtype_lower or 'double' in dtype_lower:
        return 'float'
    
    # Boolean types
    if 'bool' in dtype_lower:
        return 'boolean'
    
    # Date/datetime types
    if 'datetime' in dtype_lower or 'timestamp' in dtype_lower:
        return 'datetime'
    if 'date' in dtype_lower:
        return 'date'
    
    # String/object types (default for text data)
    if 'object' in dtype_lower or 'string' in dtype_lower or 'str' in dtype_lower:
        return 'string'
    
    # Default to string for unknown types
    return 'string'


@dataclass
class ClassificationScore:
    """Score from a single classifier."""
    confidence: float
    sensitivity_type: str
    reasoning: str
    pattern_matches: List[str] = None
    
    def __post_init__(self):
        if self.pattern_matches is None:
            self.pattern_matches = []


class PatternClassifier:
    """Classifier based on regex patterns for common PII types."""
    
    def __init__(self):
        self.patterns = {
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            'phone': [
                r'\b\d{3}[-]\d{3}[-]\d{4}\b',  # US format with dashes (strict)
                r'\b\d{3}[.]\d{3}[.]\d{4}\b',  # US format with dots (strict)
                r'\b\d{10}\b',  # US format plain 10 digits
                r'\b\+\d{1,3}[-.\s]\(?\d{1,4}\)?[-.\s]\d{1,4}[-.\s]\d{1,9}\b',  # International with +
            ],
            'ssn': [
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{9}\b',
            ],
            'credit_card': [
                r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b',
            ],
            'postal_code': [
                r'\b\d{5}(?:-\d{4})?\b',  # US ZIP
                r'\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b',  # UK postcode
            ],
            'ip_address': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            ],
            'date_of_birth': [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            ],
        }
    
    def classify(self, column_name: str, sample_values: pd.Series, data_profile: Dict[str, Any]) -> ClassificationScore:
        """Classify field based on pattern matching."""
        # Convert sample values to strings and drop nulls
        sample_strings = sample_values.dropna().astype(str).head(100)
        
        if len(sample_strings) == 0:
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No non-null values to analyze'
            )
        
        # Skip pattern matching for numeric columns (to avoid false positives like floats matching phone patterns)
        if pd.api.types.is_numeric_dtype(sample_values):
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='Numeric column - pattern matching skipped to avoid false positives'
            )
        
        # Test each pattern type
        best_match = None
        best_confidence = 0.0
        best_matches = []
        
        for pii_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                for value in sample_strings:
                    if re.search(pattern, str(value)):
                        matches.append(value)
            
            if matches:
                # Calculate confidence based on match percentage
                # Use total matches, not unique matches, to handle repeated values correctly
                match_percentage = len(matches) / len(sample_strings)
                if match_percentage > best_confidence:
                    best_confidence = match_percentage
                    best_match = pii_type
                    best_matches = list(set(matches))[:5]  # Keep first 5 unique examples
        
        if best_match:
            return ClassificationScore(
                confidence=min(best_confidence, 0.95),  # Cap at 0.95 for pattern-only
                sensitivity_type=best_match,
                reasoning=f'Pattern matching detected {best_match} format in {int(best_confidence * 100)}% of samples',
                pattern_matches=best_matches
            )
        
        return ClassificationScore(
            confidence=0.0,
            sensitivity_type='unknown',
            reasoning='No PII patterns detected'
        )


class NameBasedClassifier:
    """Classifier based on field names."""
    
    def __init__(self):
        self.name_patterns = {
            'email': ['email', 'e_mail', 'email_address', 'emailaddress'],
            'phone': ['phone', 'phone_number', 'phonenumber', 'telephone', 'contact_number', 'mobile', 'mobile_number', 'cell', 'cell_number'],
            'name': ['first_name', 'last_name', 'surname', 'given_name', 'full_name', 'firstname', 'lastname'],
            'address': ['address', 'street', 'city', 'state', 'zip', 'postal', 'country', 'postcode'],
            'ssn': ['ssn', 'social_security', 'national_id', 'tax_id'],
            'dob': ['dob', 'birth_date', 'date_of_birth', 'birthdate', 'birth_dt'],
            'credit_card': ['credit_card', 'cc_number', 'payment_card', 'card_number'],
            'password': ['password', 'passwd', 'pwd'],
            'account': ['account_number', 'account_id', 'customer_id'],
        }
    
    def classify(self, column_name: str, sample_values: pd.Series, data_profile: Dict[str, Any]) -> ClassificationScore:
        """Classify field based on column name."""
        column_lower = column_name.lower().replace('_', '').replace(' ', '')
        
        for pii_type, keywords in self.name_patterns.items():
            for keyword in keywords:
                keyword_normalized = keyword.replace('_', '').replace(' ', '')
                if keyword_normalized in column_lower:
                    return ClassificationScore(
                        confidence=0.85,
                        sensitivity_type=pii_type,
                        reasoning=f'Field name "{column_name}" contains keyword "{keyword}" indicating {pii_type}'
                    )
        
        return ClassificationScore(
            confidence=0.0,
            sensitivity_type='unknown',
            reasoning='Field name does not match known PII patterns'
        )


class ContentAnalysisClassifier:
    """Classifier based on statistical analysis of content."""
    
    def classify(self, column_name: str, sample_values: pd.Series, data_profile: Dict[str, Any]) -> ClassificationScore:
        """Classify field based on content characteristics."""
        # Drop nulls
        clean_values = sample_values.dropna()
        
        if len(clean_values) == 0:
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='No non-null values to analyze'
            )
        
        # Check if numeric
        if pd.api.types.is_numeric_dtype(clean_values):
            # Check for ID-like patterns (high cardinality, sequential)
            unique_ratio = len(clean_values.unique()) / len(clean_values)
            if unique_ratio > 0.9:
                return ClassificationScore(
                    confidence=0.6,
                    sensitivity_type='identifier',
                    reasoning=f'High cardinality ({unique_ratio:.2%}) suggests unique identifier'
                )
        
        # Check string characteristics
        if pd.api.types.is_string_dtype(clean_values) or pd.api.types.is_object_dtype(clean_values):
            str_values = clean_values.astype(str)
            
            # Check for high uniqueness (potential names, emails, etc.)
            unique_ratio = len(str_values.unique()) / len(str_values)
            
            # Check average length
            avg_length = str_values.str.len().mean()
            
            # Check for special characters
            has_special = str_values.str.contains(r'[@#$%&*]', regex=True).any()
            
            if unique_ratio > 0.8 and avg_length > 10 and has_special:
                return ClassificationScore(
                    confidence=0.5,
                    sensitivity_type='text_pii',
                    reasoning=f'High uniqueness ({unique_ratio:.2%}), long strings (avg {avg_length:.0f} chars), and special characters suggest potential PII'
                )
            
            if unique_ratio > 0.9 and avg_length < 50:
                return ClassificationScore(
                    confidence=0.4,
                    sensitivity_type='identifier',
                    reasoning=f'Very high uniqueness ({unique_ratio:.2%}) suggests unique identifier or name'
                )
        
        return ClassificationScore(
            confidence=0.0,
            sensitivity_type='unknown',
            reasoning='Content analysis did not detect PII characteristics'
        )


class ConfluenceKnowledgeClassifier:
    """Classifier that uses Confluence knowledge base and Bedrock LLM."""
    
    def __init__(self, confluence_client: Optional[ConfluenceClient] = None, bedrock_client=None):
        """Initialize Confluence knowledge classifier.
        
        Args:
            confluence_client: Confluence client for documentation queries
            bedrock_client: Bedrock client for LLM-based analysis
        """
        self.confluence_client = confluence_client
        self.bedrock_client = bedrock_client
        self._cache = {}  # Cache Confluence results to minimize API calls
    
    async def classify(self, column_name: str, sample_values: pd.Series, data_profile: Dict[str, Any]) -> ClassificationScore:
        """Classify field using Confluence documentation and Bedrock LLM.
        
        Args:
            column_name: Name of the field
            sample_values: Sample values from the field
            data_profile: Statistical profile of the field
            
        Returns:
            ClassificationScore with confidence and reasoning
        """
        # If no Confluence client available, return zero confidence
        if not self.confluence_client:
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning='Confluence client not available'
            )
        
        # Check cache first
        cache_key = column_name.lower()
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            return ClassificationScore(
                confidence=cached_result['confidence'],
                sensitivity_type=cached_result['sensitivity_type'],
                reasoning=f"Cached: {cached_result['reasoning']}",
                pattern_matches=cached_result.get('confluence_refs', [])
            )
        
        try:
            # Search Confluence for field documentation
            query = f'field definition {column_name}'
            results = await self.confluence_client.search(query, limit=5)
            
            if not results:
                return ClassificationScore(
                    confidence=0.0,
                    sensitivity_type='unknown',
                    reasoning='No Confluence documentation found for this field'
                )
            
            # If Bedrock is available, use it to analyze documentation
            if self.bedrock_client:
                return await self._analyze_with_bedrock(
                    column_name, sample_values, results
                )
            else:
                # Fallback: Simple keyword-based analysis
                return self._analyze_with_keywords(column_name, results)
                
        except Exception as e:
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning=f'Error querying Confluence: {str(e)}'
            )
    
    async def _analyze_with_bedrock(self, column_name: str, sample_values: pd.Series, 
                                   confluence_results: List) -> ClassificationScore:
        """Use Bedrock LLM to analyze Confluence documentation.
        
        Args:
            column_name: Field name
            sample_values: Sample values
            confluence_results: Confluence search results
            
        Returns:
            ClassificationScore based on LLM analysis
        """
        # Prepare context from Confluence
        context = "\n\n".join([
            f"Document: {r.title}\n{r.content[:500]}..."  # Limit content length
            for r in confluence_results[:3]  # Use top 3 results
        ])
        
        # Get sample values (limit to 10)
        samples = sample_values.dropna().astype(str).head(10).tolist()
        
        # Construct prompt for Bedrock
        prompt = f"""Analyze this field documentation and determine if the field contains sensitive personal information (PII).

Field name: {column_name}
Sample values: {samples}

Documentation from knowledge base:
{context}

Based on the field name, sample values, and documentation, determine:
1. Is this field sensitive (contains PII)?
2. What type of sensitive data is it (email, phone, name, address, ssn, etc.)?
3. How confident are you (0.0 to 1.0)?
4. What is your reasoning?

Respond with JSON in this exact format:
{{"is_sensitive": true/false, "type": "email/phone/name/etc", "confidence": 0.0-1.0, "reasoning": "explanation"}}
"""
        
        try:
            # Call Bedrock (placeholder - actual implementation would use boto3)
            # For now, return a mock response based on documentation keywords
            response = await self._mock_bedrock_call(prompt, confluence_results)
            
            # Parse response
            result = json.loads(response)
            
            # Cache the result
            cache_key = column_name.lower()
            self._cache[cache_key] = {
                'confidence': result['confidence'],
                'sensitivity_type': result['type'] if result['is_sensitive'] else 'non_sensitive',
                'reasoning': result['reasoning'],
                'confluence_refs': [r.url for r in confluence_results[:3]]
            }
            
            return ClassificationScore(
                confidence=result['confidence'],
                sensitivity_type=result['type'] if result['is_sensitive'] else 'non_sensitive',
                reasoning=f"Confluence + Bedrock: {result['reasoning']}",
                pattern_matches=[r.url for r in confluence_results[:3]]
            )
            
        except Exception as e:
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='unknown',
                reasoning=f'Error analyzing with Bedrock: {str(e)}'
            )
    
    async def _mock_bedrock_call(self, prompt: str, confluence_results: List) -> str:
        """Mock Bedrock call for demo purposes.
        
        In production, this would use boto3 to call Amazon Bedrock.
        For now, we analyze the Confluence content for PII keywords.
        """
        # Analyze Confluence content for PII indicators
        combined_content = " ".join([r.content.lower() for r in confluence_results])
        combined_titles = " ".join([r.title.lower() for r in confluence_results])
        
        # PII indicators with specific keywords (order matters - more specific first)
        pii_indicators = {
            'ssn': ['ssn', 'social security', 'national id', 'tax id', 'critical', 'highly sensitive'],
            'payment': ['payment', 'credit card', 'bank account', 'pci-dss', 'cardholder'],
            'phone': ['phone number', 'telephone', 'mobile', 'contact number'],
            'email': ['email address', 'e-mail', 'electronic mail'],
            'address': ['address field', 'street', 'location', 'postal'],
            'name': ['name field', 'first name', 'last name', 'surname', 'identity'],
            'account': ['account number', 'customer id', 'identifier'],
        }
        
        # Check for matches - prioritize title matches and specific keywords
        best_match = None
        best_score = 0
        
        for pii_type, keywords in pii_indicators.items():
            # Score based on both title and content, with title weighted higher
            title_score = sum(2 for keyword in keywords if keyword in combined_titles)
            content_score = sum(1 for keyword in keywords if keyword in combined_content)
            total_score = title_score + content_score
            
            if total_score > best_score:
                best_score = total_score
                best_match = pii_type
        
        # Determine if sensitive
        is_sensitive = best_score >= 2  # At least 2 keyword matches
        confidence = min(0.9, 0.5 + (best_score * 0.1))  # Scale confidence based on matches
        
        if is_sensitive and best_match:
            response = {
                'is_sensitive': True,
                'type': best_match,
                'confidence': confidence,
                'reasoning': f'Documentation indicates this is a {best_match} field with {best_score} PII indicators found'
            }
        else:
            response = {
                'is_sensitive': False,
                'type': 'non_sensitive',
                'confidence': 0.3,
                'reasoning': 'Documentation does not clearly indicate PII classification'
            }
        
        return json.dumps(response)
    
    def _analyze_with_keywords(self, column_name: str, confluence_results: List) -> ClassificationScore:
        """Fallback keyword-based analysis when Bedrock is not available.
        
        Args:
            column_name: Field name
            confluence_results: Confluence search results
            
        Returns:
            ClassificationScore based on keyword analysis
        """
        # Combine all content and titles
        combined_content = " ".join([r.content.lower() for r in confluence_results])
        combined_titles = " ".join([r.title.lower() for r in confluence_results])
        
        # Check for PII keywords (more specific keywords first)
        pii_keywords = {
            'ssn': ['ssn', 'social security', 'sensitive', 'critical'],
            'payment': ['payment', 'credit card', 'pci-dss'],
            'phone': ['phone number', 'telephone', 'mobile'],
            'email': ['email address', 'e-mail'],
            'name': ['name field', 'identity'],
            'address': ['address field', 'location', 'postal'],
        }
        
        # Score based on both title and content
        best_match = None
        best_score = 0
        
        for pii_type, keywords in pii_keywords.items():
            title_matches = sum(2 for keyword in keywords if keyword in combined_titles)
            content_matches = sum(1 for keyword in keywords if keyword in combined_content)
            total_matches = title_matches + content_matches
            
            if total_matches > best_score:
                best_score = total_matches
                best_match = pii_type
        
        if best_match and best_score >= 2:
            # Cache the result
            cache_key = column_name.lower()
            self._cache[cache_key] = {
                'confidence': 0.75,
                'sensitivity_type': best_match,
                'reasoning': f'Confluence documentation contains {best_score} PII indicators',
                'confluence_refs': [r.url for r in confluence_results[:3]]
            }
            
            return ClassificationScore(
                confidence=0.75,
                sensitivity_type=best_match,
                reasoning=f'Confluence documentation contains {best_score} PII indicators for {best_match}',
                pattern_matches=[r.url for r in confluence_results[:3]]
            )
        
        return ClassificationScore(
            confidence=0.2,
            sensitivity_type='unknown',
            reasoning='Confluence documentation found but no clear PII indicators'
        )


class DataProcessorAgent:
    """Agent for analyzing production data and identifying sensitive fields."""
    
    def __init__(self, confluence_client=None, bedrock_client=None, explanation_callback: Optional[Callable[[Explanation], None]] = None):
        """Initialize the Data Processor Agent.
        
        Args:
            confluence_client: Optional Confluence client for knowledge base queries
            bedrock_client: Optional Bedrock client for LLM-based classification
            explanation_callback: Optional callback function to receive explanations
        """
        self.confluence_client = confluence_client
        self.bedrock_client = bedrock_client
        self.explanation_callback = explanation_callback
        self.explanation_generator = get_explanation_generator()
        
        # Initialize classifiers
        self.classifiers = [
            ('pattern', PatternClassifier()),
            ('name', NameBasedClassifier()),
            ('content', ContentAnalysisClassifier()),
        ]
        
        # Add Confluence classifier if client is available
        if confluence_client:
            self.classifiers.append(
                ('confluence', ConfluenceKnowledgeClassifier(confluence_client, bedrock_client))
            )
    
    def _emit_explanation(self, action: str, context: Dict[str, Any]):
        """Emit an explanation for an action.
        
        Args:
            action: Action being performed
            context: Context data for the explanation
        """
        if self.explanation_callback:
            explanation = self.explanation_generator.generate('data_processor', action, context)
            self.explanation_callback(explanation)
    
    def load_data(self, data_file: Path) -> pd.DataFrame:
        """Load data from file."""
        file_ext = data_file.suffix.lower()
        
        if file_ext == '.csv':
            return pd.read_csv(data_file)
        elif file_ext == '.json':
            return pd.read_json(data_file)
        elif file_ext == '.parquet':
            return pd.read_parquet(data_file)
        else:
            raise ValueError(f'Unsupported file format: {file_ext}')
    
    def profile_data(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Create statistical profile of the data."""
        profile = {}
        
        for column in df.columns:
            # Handle empty dataframes
            if len(df) == 0:
                col_profile = {
                    'dtype': str(df[column].dtype),
                    'null_count': 0,
                    'null_percentage': 0.0,
                    'unique_count': 0,
                    'unique_percentage': 0.0,
                }
            else:
                col_profile = {
                    'dtype': str(df[column].dtype),
                    'null_count': int(df[column].isnull().sum()),
                    'null_percentage': float(df[column].isnull().sum() / len(df)),
                    'unique_count': int(df[column].nunique()),
                    'unique_percentage': float(df[column].nunique() / len(df)),
                }
            
            # Add numeric statistics
            if pd.api.types.is_numeric_dtype(df[column]):
                col_profile.update({
                    'mean': float(df[column].mean()) if not df[column].isnull().all() else None,
                    'std': float(df[column].std()) if not df[column].isnull().all() else None,
                    'min': float(df[column].min()) if not df[column].isnull().all() else None,
                    'max': float(df[column].max()) if not df[column].isnull().all() else None,
                })
            
            # Add string statistics
            if pd.api.types.is_string_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]):
                str_col = df[column].dropna().astype(str)
                if len(str_col) > 0:
                    col_profile.update({
                        'avg_length': float(str_col.str.len().mean()),
                        'max_length': int(str_col.str.len().max()),
                        'min_length': int(str_col.str.len().min()),
                    })
            
            profile[column] = col_profile
        
        return profile
    
    def aggregate_scores(self, scores: Dict[str, ClassificationScore]) -> ClassificationScore:
        """Aggregate scores from multiple classifiers."""
        # Filter out zero-confidence scores
        valid_scores = {name: score for name, score in scores.items() if score.confidence > 0}
        
        if not valid_scores:
            return ClassificationScore(
                confidence=0.0,
                sensitivity_type='non_sensitive',
                reasoning='No classifier detected sensitive data'
            )
        
        # Choose the sensitivity type from the highest confidence classifier
        best_classifier = max(valid_scores.items(), key=lambda x: x[1].confidence)
        best_score = best_classifier[1]
        
        # Use a more sophisticated aggregation strategy:
        # 1. If any classifier has very high confidence (>0.8), use that as a strong signal
        # 2. If name-based classifier detects PII name, boost the confidence
        # 3. If pattern matching has good confidence (>0.65), boost it
        # 4. Otherwise use weighted average
        
        max_confidence = max(score.confidence for score in valid_scores.values())
        
        # Strong signal from any classifier
        if max_confidence > 0.8:
            final_confidence = max_confidence
        # Name-based classifier found PII-indicating name
        elif 'name' in valid_scores and valid_scores['name'].confidence >= 0.8:
            # Give strong weight to name-based classification
            # Combine with other signals but ensure we stay above threshold
            name_conf = valid_scores['name'].confidence
            other_confs = [s.confidence for n, s in valid_scores.items() if n != 'name']
            if other_confs:
                # Weighted: 70% name, 30% average of others
                final_confidence = 0.7 * name_conf + 0.3 * (sum(other_confs) / len(other_confs))
            else:
                final_confidence = name_conf
        # Pattern matching has good confidence (likely PII)
        elif 'pattern' in valid_scores and valid_scores['pattern'].confidence >= 0.55:
            # When pattern matching shows strong PII signals, use it directly
            # Pattern matching is the most reliable indicator of PII
            final_confidence = valid_scores['pattern'].confidence
        else:
            # Use weighted average with adjusted weights
            weights = {
                'pattern': 0.5,
                'name': 0.3,
                'content': 0.2,
            }
            
            # Calculate weighted confidence
            total_confidence = 0.0
            total_weight = 0.0
            
            for classifier_name, score in valid_scores.items():
                weight = weights.get(classifier_name, 0.1)
                total_confidence += score.confidence * weight
                total_weight += weight
            
            final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        
        # Combine reasoning from all classifiers
        reasoning_parts = [f'{name}: {score.reasoning}' for name, score in valid_scores.items()]
        combined_reasoning = '; '.join(reasoning_parts)
        
        # Collect all pattern matches
        all_patterns = []
        for score in valid_scores.values():
            if score.pattern_matches:
                all_patterns.extend(score.pattern_matches)
        
        return ClassificationScore(
            confidence=final_confidence,
            sensitivity_type=best_score.sensitivity_type,
            reasoning=combined_reasoning,
            pattern_matches=all_patterns[:5]  # Keep first 5
        )
    
    async def select_strategy_with_bedrock(
        self, 
        field_name: str,
        score: ClassificationScore, 
        is_sensitive: bool,
        sample_values: List[str]
    ) -> str:
        """Use Claude Haiku to intelligently select the best synthesis strategy.
        
        Args:
            field_name: Name of the field
            score: Classification score with sensitivity type and confidence
            is_sensitive: Whether the field is classified as sensitive
            sample_values: Sample values from the field
            
        Returns:
            Strategy name: 'bedrock_llm', 'sdv_preserve_distribution', or 'sdv_gaussian_copula'
        """
        # For non-sensitive fields, always use SDV
        if not is_sensitive:
            return 'sdv_preserve_distribution'
        
        # Use Claude Haiku to analyze the field and recommend strategy
        try:
            from shared.utils.bedrock_client import BedrockClient, BedrockConfig
            
            config = BedrockConfig(
                model_id='anthropic.claude-3-haiku-20240307-v1:0',  # Use Haiku for cost efficiency
                max_tokens=200,
                temperature=0.0
            )
            client = BedrockClient(config)
            
            # Prepare sample values for analysis (limit to 10 examples)
            samples_str = "\n".join([f"- {val}" for val in sample_values[:10]])
            
            prompt = f"""Analyze this data field and recommend the best synthesis strategy.

Field Name: {field_name}
Sensitivity Type: {score.sensitivity_type}
Confidence: {score.confidence:.2f}
Sample Values:
{samples_str}

Available Strategies:
1. bedrock_llm - Use AI to generate realistic, contextual synthetic data. Best for text-based PII like names, addresses, emails, phone numbers.
2. sdv_preserve_distribution - Use statistical methods to preserve data distributions. Best for numeric identifiers, codes, or structured data.
3. sdv_gaussian_copula - Advanced statistical modeling for complex relationships. Best for fields with intricate correlations.

Respond with ONLY the strategy name (bedrock_llm, sdv_preserve_distribution, or sdv_gaussian_copula) and nothing else."""

            # Use generate_text_field with asyncio.to_thread for async execution
            response = await asyncio.to_thread(
                client.generate_text_field,
                field_name="strategy_recommendation",
                num_values=1,
                context=prompt
            )
            strategy = response[0].strip().lower() if response else "sdv_preserve_distribution"
            
            # Validate response
            valid_strategies = {'bedrock_llm', 'sdv_preserve_distribution', 'sdv_gaussian_copula'}
            if strategy in valid_strategies:
                return strategy
            
            # Fallback if invalid response
            return self.select_strategy_fallback(score, is_sensitive)
            
        except Exception as e:
            # Fallback to rule-based selection if Bedrock fails
            print(f"Bedrock strategy selection failed: {e}, using fallback")
            return self.select_strategy_fallback(score, is_sensitive)
    
    def select_strategy_fallback(self, score: ClassificationScore, is_sensitive: bool) -> str:
        """Fallback strategy selection using rules.
        
        Args:
            score: Classification score with sensitivity type and confidence
            is_sensitive: Whether the field is classified as sensitive
            
        Returns:
            Strategy name: 'bedrock_llm', 'sdv_preserve_distribution', or 'sdv_gaussian_copula'
        """
        # For non-sensitive fields, always use SDV
        if not is_sensitive:
            return 'sdv_preserve_distribution'
        
        # For sensitive fields, use Bedrock LLM for text-based PII that needs realistic generation
        text_based_pii = {
            'email', 'phone', 'name', 'address', 'text_pii', 
            'ssn', 'credit_card', 'dob', 'postal_code', 'password'
        }
        
        if score.sensitivity_type in text_based_pii:
            return 'bedrock_llm'
        
        # For other sensitive fields (identifiers, etc.), use SDV to preserve distributions
        return 'sdv_preserve_distribution'
    
    async def process_async(self, data_file: Path) -> SensitivityReport:
        """Process production data asynchronously and generate sensitivity report.
        
        Args:
            data_file: Path to production data file
            
        Returns:
            SensitivityReport with field classifications
        """
        # Load and profile data
        df = self.load_data(data_file)
        profile = self.profile_data(df)
        
        # Capture original column order
        column_order = list(df.columns)
        logger.info(f"Captured column order: {column_order}")
        
        # Emit start explanation
        self._emit_explanation('start_analysis', {
            'num_columns': len(df.columns),
            'num_rows': len(df)
        })
        
        # Classify each field
        classifications = {}
        
        for column in df.columns:
            # Emit field classification start
            self._emit_explanation('field_classification', {
                'field_name': column
            })
            # Run all classifiers
            scores = {}
            confluence_refs = []
            
            for classifier_name, classifier in self.classifiers:
                # Check if classifier has async classify method
                if hasattr(classifier, 'classify') and classifier_name == 'confluence':
                    score = await classifier.classify(
                        column_name=column,
                        sample_values=df[column],
                        data_profile=profile[column]
                    )
                else:
                    score = classifier.classify(
                        column_name=column,
                        sample_values=df[column],
                        data_profile=profile[column]
                    )
                scores[classifier_name] = score
                
                # Collect Confluence references
                if score.pattern_matches and classifier_name == 'confluence':
                    confluence_refs.extend(score.pattern_matches)
            
            # Aggregate scores
            final_score = self.aggregate_scores(scores)
            
            # Get user-friendly data type
            pandas_dtype = profile[column].get('dtype', 'object')
            friendly_dtype = map_pandas_dtype_to_friendly_name(pandas_dtype)
            
            # Determine if field is sensitive
            is_sensitive = final_score.confidence >= 0.7
            
            # Get sample values for strategy selection
            sample_values = df[column].dropna().astype(str).head(10).tolist()
            
            # Use Bedrock to select the best strategy
            recommended_strategy = await self.select_strategy_with_bedrock(
                field_name=column,
                score=final_score,
                is_sensitive=is_sensitive,
                sample_values=sample_values
            )
            
            # Create classification
            classifications[column] = FieldClassification(
                field_name=column,
                is_sensitive=is_sensitive,
                sensitivity_type=final_score.sensitivity_type,
                confidence=final_score.confidence,
                reasoning=final_score.reasoning,
                recommended_strategy=recommended_strategy,
                data_type=friendly_dtype,
                confluence_references=confluence_refs,
                pattern_matches=final_score.pattern_matches if final_score.pattern_matches else []
            )
        
        # Calculate statistics
        sensitive_count = sum(1 for c in classifications.values() if c.is_sensitive)
        
        # Calculate confidence distribution
        confidence_dist = {'high': 0, 'medium': 0, 'low': 0}
        for classification in classifications.values():
            if classification.confidence >= 0.8:
                confidence_dist['high'] += 1
            elif classification.confidence >= 0.5:
                confidence_dist['medium'] += 1
            else:
                confidence_dist['low'] += 1
        
        return SensitivityReport(
            classifications=classifications,
            data_profile=profile,
            timestamp=datetime.now(),
            total_fields=len(classifications),
            sensitive_fields=sensitive_count,
            confidence_distribution=confidence_dist,
            column_order=column_order
        )
    
    def process(self, data_file: Path) -> SensitivityReport:
        """Process production data and generate sensitivity report (synchronous wrapper).
        
        Args:
            data_file: Path to production data file
            
        Returns:
            SensitivityReport with field classifications
        """
        # For synchronous usage, run the async version in an event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process_async(data_file))
