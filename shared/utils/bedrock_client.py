"""Amazon Bedrock client wrapper for text field generation."""

import json
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class BedrockConfig:
    """Configuration for Bedrock text generation."""
    model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'
    temperature: float = 0.9
    max_tokens: int = 2000
    top_p: float = 0.9
    batch_size: int = 100
    max_retries: int = 3
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 16.0


class BedrockClient:
    """Wrapper for Amazon Bedrock API with retry logic and batching."""
    
    def __init__(self, bedrock_runtime_client, config: Optional[BedrockConfig] = None, agent_logger=None):
        """Initialize Bedrock client.
        
        Args:
            bedrock_runtime_client: boto3 bedrock-runtime client
            config: Optional BedrockConfig for generation parameters
            agent_logger: Optional AgentLogger for structured logging
        """
        self.client = bedrock_runtime_client
        self.config = config or BedrockConfig()
        self.agent_logger = agent_logger
        
        logger.info(
            f"Initialized Bedrock client with model: {self.config.model_id}, "
            f"batch_size: {self.config.batch_size}"
        )
    
    def invoke(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Invoke Bedrock model with retry logic.
        
        Args:
            prompt: Input prompt for the model
            model_id: Optional model ID (overrides config)
            temperature: Optional temperature (overrides config)
            max_tokens: Optional max tokens (overrides config)
            **kwargs: Additional model parameters
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all retry attempts fail
        """
        model_id = model_id or self.config.model_id
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        # Prepare request body based on model provider
        if 'anthropic' in model_id.lower():
            body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': kwargs.get('top_p', self.config.top_p)
            }
        else:
            # Generic format for other models
            body = {
                'prompt': prompt,
                'temperature': temperature,
                'max_tokens': max_tokens,
                **kwargs
            }
        
        # Retry with exponential backoff
        retry_count = 0
        last_exception = None
        
        while retry_count <= self.config.max_retries:
            try:
                logger.debug(f"Invoking Bedrock model {model_id} (attempt {retry_count + 1})")
                
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                
                # Extract text based on model provider
                if 'anthropic' in model_id.lower():
                    text = response_body['content'][0]['text']
                else:
                    # Generic extraction
                    text = response_body.get('completion', response_body.get('text', ''))
                
                logger.debug(f"Successfully invoked Bedrock model (attempt {retry_count + 1})")
                return text
                
            except Exception as e:
                last_exception = e
                retry_count += 1
                
                if retry_count > self.config.max_retries:
                    logger.error(
                        f"Bedrock invocation failed after {self.config.max_retries} retries: {e}"
                    )
                    raise
                
                # Calculate exponential backoff delay
                delay = min(
                    self.config.initial_retry_delay * (2 ** (retry_count - 1)),
                    self.config.max_retry_delay
                )
                
                # Add jitter to prevent thundering herd
                delay = delay * (0.5 + random.random() * 0.5)
                
                logger.warning(
                    f"Bedrock invocation failed (attempt {retry_count}), "
                    f"retrying in {delay:.2f}s: {e}"
                )
                
                time.sleep(delay)
        
        # Should not reach here, but just in case
        raise last_exception
    
    def generate_text_field_batch(
        self,
        field_name: str,
        field_type: str,
        num_values: int,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate a batch of text field values using Bedrock.
        
        Args:
            field_name: Name of the field being generated
            field_type: Type of field (e.g., 'name', 'email', 'address')
            num_values: Number of values to generate
            context: Optional context from related fields
            constraints: Optional constraints (patterns, formats, etc.)
            
        Returns:
            List of generated text values
            
        Raises:
            Exception: If generation fails after retries
        """
        logger.info(
            f"Generating {num_values} values for field '{field_name}' "
            f"(type: {field_type})"
        )
        
        # Build prompt with context and constraints
        prompt = self._build_prompt(
            field_name=field_name,
            field_type=field_type,
            num_values=min(num_values, self.config.batch_size),
            context=context,
            constraints=constraints
        )
        
        try:
            # Invoke Bedrock
            response = self.invoke(prompt)
            
            # Parse JSON response
            values = self._parse_response(response, num_values)
            
            logger.info(f"Successfully generated {len(values)} values for '{field_name}'")
            
            return values
            
        except Exception as e:
            logger.error(f"Failed to generate text field '{field_name}': {e}")
            raise
    
    def generate_from_examples(
        self,
        field_name: str,
        examples: List[str],
        num_values: int,
        fallback_generator: Optional[callable] = None
    ) -> List[str]:
        """Generate values based on user-provided examples using Claude Haiku.
        
        Args:
            field_name: Name of the field being generated
            examples: List of example values provided by the user
            num_values: Number of values to generate
            fallback_generator: Optional fallback function if Bedrock fails
            
        Returns:
            List of generated values matching the pattern of examples
        """
        if not examples or len(examples) < 3:
            raise ValueError("At least 3 examples are required for example-based generation")
        
        results = []
        remaining = num_values
        
        # Process in batches
        while remaining > 0:
            batch_size = min(remaining, self.config.batch_size)
            
            try:
                # Build prompt with examples
                examples_str = "\n".join([f"- {ex}" for ex in examples])
                
                prompt = f"""Analyze these example values for the field '{field_name}' and generate {batch_size} new similar values:

Examples:
{examples_str}

Instructions:
1. Identify the pattern, format, and style of the examples
2. Generate {batch_size} NEW values that match the same pattern
3. Ensure values are diverse but consistent with the examples
4. Return ONLY the generated values, one per line, no explanations

Generated values:"""

                # Log the prompt if agent_logger is available
                if self.agent_logger:
                    self.agent_logger.info(
                        f"Sending prompt to Claude for field '{field_name}' (example-based generation)",
                        metadata={
                            'field_name': field_name,
                            'model': 'anthropic.claude-3-haiku-20240307-v1:0',
                            'batch_size': batch_size,
                            'num_examples': len(examples),
                            'prompt': prompt
                        }
                    )

                response = self.invoke(
                    prompt=prompt,
                    model_id='anthropic.claude-3-haiku-20240307-v1:0',  # Use Haiku for cost efficiency
                    temperature=0.8,
                    max_tokens=2000
                )
                
                # Parse response - split by newlines and clean
                generated = [
                    line.strip().lstrip('-').strip() 
                    for line in response.strip().split('\n') 
                    if line.strip() and not line.strip().startswith('#')
                ]
                
                # Filter out empty values
                generated = [v for v in generated if v]
                
                if generated:
                    results.extend(generated[:batch_size])
                    remaining -= len(generated[:batch_size])
                else:
                    raise ValueError("No valid values generated from examples")
                    
            except Exception as e:
                logger.error(
                    f"Example-based generation failed for '{field_name}': {e}, "
                    f"remaining: {remaining}"
                )
                
                # Use fallback if available
                if fallback_generator:
                    logger.info(f"Using fallback generator for '{field_name}'")
                    fallback_values = fallback_generator(
                        field_name=field_name,
                        field_type='custom',
                        num_values=remaining
                    )
                    results.extend(fallback_values)
                    remaining = 0
                else:
                    # Re-raise if no fallback
                    raise
        
        return results[:num_values]
    
    def generate_text_field(
        self,
        field_name: str,
        field_type: str,
        num_values: int,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        fallback_generator: Optional[callable] = None
    ) -> List[str]:
        """Generate text field values with batching and fallback.
        
        Args:
            field_name: Name of the field being generated
            field_type: Type of field (e.g., 'name', 'email', 'address')
            num_values: Number of values to generate
            context: Optional context from related fields
            constraints: Optional constraints (patterns, formats, etc.)
            fallback_generator: Optional fallback function if Bedrock fails
            
        Returns:
            List of generated text values
        """
        results = []
        remaining = num_values
        
        # Process in batches
        while remaining > 0:
            batch_size = min(remaining, self.config.batch_size)
            
            try:
                batch_results = self.generate_text_field_batch(
                    field_name=field_name,
                    field_type=field_type,
                    num_values=batch_size,
                    context=context,
                    constraints=constraints
                )
                
                results.extend(batch_results[:batch_size])
                remaining -= len(batch_results[:batch_size])
                
            except Exception as e:
                logger.error(
                    f"Batch generation failed for '{field_name}', "
                    f"remaining: {remaining}"
                )
                
                # Use fallback if available
                if fallback_generator:
                    logger.info(f"Using fallback generator for '{field_name}'")
                    fallback_values = fallback_generator(
                        field_name=field_name,
                        field_type=field_type,
                        num_values=remaining
                    )
                    results.extend(fallback_values)
                    remaining = 0
                else:
                    # Re-raise if no fallback
                    raise
        
        return results[:num_values]
    
    def _build_prompt(
        self,
        field_name: str,
        field_type: str,
        num_values: int,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for text field generation.
        
        Args:
            field_name: Name of the field
            field_type: Type of field
            num_values: Number of values to generate
            context: Optional context from related fields
            constraints: Optional constraints
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"Generate {num_values} realistic synthetic {field_type} values for a field named '{field_name}'.",
            f"These should be diverse, realistic, and appropriate for a {field_type} field.",
        ]
        
        # Add context if provided
        if context:
            prompt_parts.append("\nContext from related fields:")
            for key, value in context.items():
                if isinstance(value, (list, tuple)) and len(value) > 0:
                    # Show first few examples
                    examples = value[:3]
                    prompt_parts.append(f"  - {key}: {examples}")
                elif value is not None:
                    prompt_parts.append(f"  - {key}: {value}")
        
        # Add constraints if provided
        if constraints:
            prompt_parts.append("\nConstraints:")
            for key, value in constraints.items():
                prompt_parts.append(f"  - {key}: {value}")
        
        # Add output format instruction
        prompt_parts.append(
            f"\nReturn ONLY a valid JSON array with exactly {num_values} string values, "
            "no additional text or explanation. Format: [\"value1\", \"value2\", ...]"
        )
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response: str, expected_count: int) -> List[str]:
        """Parse JSON response from Bedrock.
        
        Args:
            response: Raw response text
            expected_count: Expected number of values
            
        Returns:
            List of parsed values
            
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to extract JSON array from response
            # Handle cases where model adds extra text
            response = response.strip()
            
            # Find JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON array found in response")
            
            json_str = response[start_idx:end_idx + 1]
            values = json.loads(json_str)
            
            if not isinstance(values, list):
                raise ValueError("Response is not a JSON array")
            
            # Convert all values to strings
            values = [str(v) for v in values]
            
            logger.debug(f"Parsed {len(values)} values from response")
            
            return values
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            logger.debug(f"Response was: {response[:200]}...")
            raise ValueError(f"Invalid JSON response from Bedrock: {e}")


class RuleBasedTextGenerator:
    """Fallback rule-based text generator for when Bedrock fails."""
    
    def __init__(self):
        """Initialize rule-based generator."""
        from faker import Faker
        self.faker = Faker()
        
        # Map field types to Faker methods
        self.generators = {
            'name': self.faker.name,
            'first_name': self.faker.first_name,
            'last_name': self.faker.last_name,
            'email': self.faker.email,
            'phone': self.faker.phone_number,
            'address': self.faker.address,
            'street_address': self.faker.street_address,
            'city': self.faker.city,
            'state': self.faker.state,
            'country': self.faker.country,
            'postcode': self.faker.postcode,
            'company': self.faker.company,
            'job': self.faker.job,
            'text': self.faker.text,
            'sentence': self.faker.sentence,
            'paragraph': self.faker.paragraph,
        }
        
        logger.info("Initialized rule-based text generator with Faker")
    
    def generate(
        self,
        field_name: str,
        field_type: str,
        num_values: int
    ) -> List[str]:
        """Generate values using rule-based approach.
        
        Args:
            field_name: Name of the field
            field_type: Type of field
            num_values: Number of values to generate
            
        Returns:
            List of generated values
        """
        logger.info(
            f"Generating {num_values} values for '{field_name}' "
            f"using rule-based generator"
        )
        
        # Get appropriate generator
        generator = self.generators.get(
            field_type.lower(),
            self.faker.text  # Default fallback
        )
        
        # Generate values
        values = []
        for _ in range(num_values):
            try:
                value = generator()
                values.append(str(value))
            except Exception as e:
                logger.warning(f"Rule-based generation failed: {e}")
                # Use a simple fallback
                values.append(f"{field_type}_{len(values) + 1}")
        
        return values
