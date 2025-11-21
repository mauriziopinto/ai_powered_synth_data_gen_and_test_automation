"""Test Case Agent for generating test cases from Jira scenarios."""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TestFramework(Enum):
    """Supported test automation frameworks."""
    ROBOT_FRAMEWORK = "robot"
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"


@dataclass
class TestCaseConfig:
    """Configuration for test case generation."""
    jira_url: str
    jira_username: str
    jira_api_token: str
    jira_project_key: str
    test_tag: str
    framework: str = "robot"  # robot, selenium, playwright
    output_dir: str = "tests/generated"
    use_mock: bool = False
    use_bedrock: bool = False  # Use Bedrock AI for test generation
    bedrock_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def __post_init__(self):
        # Validate framework
        if self.framework not in ['robot', 'selenium', 'playwright']:
            raise ValueError(f"Unsupported framework: {self.framework}")


@dataclass
class TestCase:
    """Represents a generated test case."""
    id: str
    name: str
    description: str
    framework: str
    code: str
    data_references: List[str] = field(default_factory=list)
    jira_key: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'framework': self.framework,
            'code': self.code,
            'data_references': self.data_references,
            'jira_key': self.jira_key,
            'created_at': self.created_at.isoformat()
        }



class TestCaseAgent:
    """Agent for generating test cases from Jira scenarios."""
    
    def __init__(self, config: TestCaseConfig):
        """Initialize test case agent.
        
        Args:
            config: Test case configuration
        """
        self.config = config
        self.jira_client = None
        self._initialize_jira_client()
        
        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _initialize_jira_client(self):
        """Initialize Jira client (real or mock)."""
        if self.config.use_mock:
            from shared.utils.jira_client import MockJiraClient
            self.jira_client = MockJiraClient()
            logger.info("Initialized mock Jira client")
        else:
            from shared.utils.jira_client import JiraClient, JiraConfig
            
            jira_config = JiraConfig(
                url=self.config.jira_url,
                username=self.config.jira_username,
                api_token=self.config.jira_api_token,
                project_key=self.config.jira_project_key
            )
            
            self.jira_client = JiraClient(jira_config)
            logger.info("Initialized Jira client")
    
    async def process(self) -> List[TestCase]:
        """Process test case generation from Jira scenarios.
        
        Returns:
            List of generated test cases
        """
        logger.info(f"Retrieving test scenarios with tag '{self.config.test_tag}'")
        
        # Retrieve test scenarios from Jira
        scenarios = self.jira_client.get_test_scenarios_by_tag(self.config.test_tag)
        
        logger.info(f"Found {len(scenarios)} test scenarios")
        
        # Generate test cases
        test_cases = []
        for scenario in scenarios:
            test_case = await self._generate_test_case(scenario)
            test_cases.append(test_case)
            
            # Save test case
            self._save_test_case(test_case)
        
        logger.info(f"Generated {len(test_cases)} test cases")
        return test_cases
    
    async def _generate_test_case(self, scenario) -> TestCase:
        """Generate test case from Jira scenario.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            Generated test case
        """
        logger.info(f"Generating test case for {scenario.key}: {scenario.summary}")
        
        # Try Bedrock-powered generation first, fall back to template-based
        use_bedrock = getattr(self.config, 'use_bedrock', False)
        
        if use_bedrock:
            try:
                code = await self._generate_with_bedrock(scenario)
            except Exception as e:
                logger.warning(f"Bedrock generation failed, falling back to templates: {str(e)}")
                code = self._generate_with_template(scenario)
        else:
            code = self._generate_with_template(scenario)
        
        # Extract data references
        data_refs = self._extract_data_references(scenario)
        
        test_case = TestCase(
            id=scenario.key,
            name=scenario.summary,
            description=scenario.description,
            framework=self.config.framework,
            code=code,
            data_references=data_refs,
            jira_key=scenario.key
        )
        
        return test_case
    
    def _generate_with_template(self, scenario) -> str:
        """Generate test code using templates.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            Generated test code
        """
        if self.config.framework == 'robot':
            return self._generate_robot_code(scenario)
        elif self.config.framework == 'selenium':
            return self._generate_selenium_code(scenario)
        elif self.config.framework == 'playwright':
            return self._generate_playwright_code(scenario)
        else:
            raise ValueError(f"Unsupported framework: {self.config.framework}")
    
    async def _generate_with_bedrock(self, scenario) -> str:
        """Generate test code using Bedrock AI.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            AI-generated test code
        """
        from shared.utils.bedrock_client import BedrockClient
        
        # Initialize Bedrock client if not already done
        if not hasattr(self, 'bedrock_client'):
            self.bedrock_client = BedrockClient()
        
        # Build prompt for test generation
        prompt = self._build_test_generation_prompt(scenario)
        
        # Generate code with Bedrock
        response = await self.bedrock_client.generate_text(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.3  # Lower temperature for more deterministic code
        )
        
        # Extract code from response
        code = self._extract_code_from_response(response)
        
        return code
    
    def _build_test_generation_prompt(self, scenario) -> str:
        """Build prompt for Bedrock test generation.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            Prompt string
        """
        framework_instructions = {
            'robot': """Generate a Robot Framework test case with:
- Proper *** Settings ***, *** Variables ***, and *** Test Cases *** sections
- SeleniumLibrary for web automation
- Clear test steps with keywords
- Appropriate assertions""",
            'selenium': """Generate a Selenium (Python) test case with:
- pytest framework
- Proper class and method structure
- WebDriver setup and teardown
- Explicit waits and assertions
- Page Object Model pattern where appropriate""",
            'playwright': """Generate a Playwright (Python) test case with:
- pytest framework
- Proper function structure with Page fixture
- Modern async/await patterns
- Built-in auto-waiting
- Strong assertions with expect()"""
        }
        
        instructions = framework_instructions.get(self.config.framework, '')
        
        prompt = f"""You are an expert test automation engineer. Generate a complete, executable test case based on the following test scenario.

Test Scenario:
Title: {scenario.summary}
Description: {scenario.description}

{f"Preconditions: {scenario.preconditions}" if scenario.preconditions else ""}

{f"Test Steps:" if scenario.test_steps else ""}
{chr(10).join([f"{i+1}. {step.get('action', '')}" for i, step in enumerate(scenario.test_steps)]) if scenario.test_steps else ""}

{f"Expected Outcome: {scenario.expected_outcome}" if scenario.expected_outcome else ""}

Framework: {self.config.framework.upper()}

{instructions}

Requirements:
1. Generate ONLY the test code, no explanations
2. Include all necessary imports
3. Make the test executable and complete
4. Add comments for clarity
5. Include proper assertions for expected outcomes
6. Handle common edge cases
7. Use data references like {{{{data.field_name}}}} where synthetic data should be used

Generate the complete test code:"""
        
        return prompt
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from Bedrock response.
        
        Args:
            response: Bedrock response text
        
        Returns:
            Extracted code
        """
        # Look for code blocks
        import re
        
        # Try to find code in markdown code blocks
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the whole response
        return response.strip()

    
    def _generate_robot_code(self, scenario) -> str:
        """Generate Robot Framework test code.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            Robot Framework test code
        """
        code = f"""*** Settings ***
Library    SeleniumLibrary
Library    Collections

*** Variables ***
${{BASE_URL}}    http://localhost:8080

*** Test Cases ***
{scenario.summary}
    [Documentation]    {scenario.description.split(chr(10))[0] if scenario.description else ''}
    [Tags]    {' '.join(scenario.tags)}
    
"""
        
        # Add preconditions as setup
        if scenario.preconditions:
            code += f"    # Preconditions: {scenario.preconditions}\n"
        
        # Add test steps
        if scenario.test_steps:
            for i, step in enumerate(scenario.test_steps, 1):
                action = step.get('action', '')
                code += f"    # Step {i}: {action}\n"
                code += f"    Log    Executing: {action}\n"
        else:
            code += "    Log    Test implementation needed\n"
        
        # Add expected outcome verification
        if scenario.expected_outcome:
            code += f"\n    # Expected: {scenario.expected_outcome}\n"
            code += "    Log    Verifying expected outcome\n"
        
        return code
    
    def _generate_selenium_code(self, scenario) -> str:
        """Generate Selenium (Python) test code.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            Selenium test code
        """
        code = f"""import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Test{scenario.key.replace('-', '_')}:
    \"\"\"
    {scenario.summary}
    
    {scenario.description.split(chr(10))[0] if scenario.description else ''}
    \"\"\"
    
    @pytest.fixture
    def driver(self):
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_{scenario.key.lower().replace('-', '_')}(self, driver):
        \"\"\"Test: {scenario.summary}\"\"\"
        
"""
        
        # Add preconditions
        if scenario.preconditions:
            code += f"        # Preconditions: {scenario.preconditions}\n"
        
        # Add test steps
        if scenario.test_steps:
            for i, step in enumerate(scenario.test_steps, 1):
                action = step.get('action', '')
                code += f"        # Step {i}: {action}\n"
                code += f"        # TODO: Implement step\n"
        else:
            code += "        # TODO: Implement test steps\n"
            code += "        pass\n"
        
        # Add expected outcome
        if scenario.expected_outcome:
            code += f"\n        # Expected: {scenario.expected_outcome}\n"
            code += "        # TODO: Add assertions\n"
        
        return code
    
    def _generate_playwright_code(self, scenario) -> str:
        """Generate Playwright (Python) test code.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            Playwright test code
        """
        code = f"""import pytest
from playwright.sync_api import Page, expect


def test_{scenario.key.lower().replace('-', '_')}(page: Page):
    \"\"\"
    {scenario.summary}
    
    {scenario.description.split(chr(10))[0] if scenario.description else ''}
    \"\"\"
    
"""
        
        # Add preconditions
        if scenario.preconditions:
            code += f"    # Preconditions: {scenario.preconditions}\n"
        
        # Add test steps
        if scenario.test_steps:
            for i, step in enumerate(scenario.test_steps, 1):
                action = step.get('action', '')
                code += f"    # Step {i}: {action}\n"
                code += f"    # TODO: Implement step\n"
        else:
            code += "    # TODO: Implement test steps\n"
            code += "    pass\n"
        
        # Add expected outcome
        if scenario.expected_outcome:
            code += f"\n    # Expected: {scenario.expected_outcome}\n"
            code += "    # TODO: Add assertions\n"
        
        return code
    
    def _extract_data_references(self, scenario) -> List[str]:
        """Extract data references from scenario.
        
        Args:
            scenario: Jira test scenario
        
        Returns:
            List of data reference identifiers
        """
        # Look for data references in description and tags
        data_refs = []
        
        # Check tags for data references
        for tag in scenario.tags:
            if tag.startswith('data-'):
                data_refs.append(tag)
        
        # Check description for data references (e.g., {{data.field_name}})
        import re
        if scenario.description:
            matches = re.findall(r'\{\{data\.(\w+)\}\}', scenario.description)
            data_refs.extend(matches)
        
        return data_refs
    
    def map_data_to_test(
        self,
        test_case: TestCase,
        synthetic_data: Dict[str, Any]
    ) -> str:
        """Map synthetic data to test case code.
        
        Args:
            test_case: Test case with data references
            synthetic_data: Dictionary of synthetic data
        
        Returns:
            Test code with data references replaced
        """
        code = test_case.code
        
        # Replace data references with actual values
        for ref in test_case.data_references:
            # Handle both {{data.field}} and data-field formats
            field_name = ref.replace('data-', '')
            
            if field_name in synthetic_data:
                value = synthetic_data[field_name]
                
                # Replace {{data.field}} pattern
                code = code.replace(f'{{{{data.{field_name}}}}}', str(value))
                
                # Replace DATA_FIELD variable pattern (for Robot Framework)
                code = code.replace(f'${{{{DATA_{field_name.upper()}}}}}', str(value))
        
        return code
    
    def _save_test_case(self, test_case: TestCase) -> None:
        """Save test case to file.
        
        Args:
            test_case: Test case to save
        """
        # Determine file extension
        ext_map = {
            'robot': '.robot',
            'selenium': '.py',
            'playwright': '.py'
        }
        ext = ext_map.get(test_case.framework, '.txt')
        
        # Create filename
        filename = f"{test_case.id.lower().replace('-', '_')}{ext}"
        filepath = Path(self.config.output_dir) / filename
        
        # Write code
        filepath.write_text(test_case.code)
        logger.info(f"Saved test case to {filepath}")
        
        # Save metadata
        metadata_file = Path(self.config.output_dir) / f"{test_case.id.lower().replace('-', '_')}.json"
        metadata_file.write_text(json.dumps(test_case.to_dict(), indent=2))
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """Retrieve a saved test case.
        
        Args:
            test_id: Test case ID
        
        Returns:
            Test case if found, None otherwise
        """
        metadata_file = Path(self.config.output_dir) / f"{test_id.lower().replace('-', '_')}.json"
        
        if not metadata_file.exists():
            return None
        
        data = json.loads(metadata_file.read_text())
        
        return TestCase(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            framework=data['framework'],
            code=data['code'],
            data_references=data.get('data_references', []),
            jira_key=data.get('jira_key'),
            created_at=datetime.fromisoformat(data['created_at'])
        )
    
    def list_test_cases(self) -> List[str]:
        """List all generated test case IDs.
        
        Returns:
            List of test case IDs
        """
        output_dir = Path(self.config.output_dir)
        
        if not output_dir.exists():
            return []
        
        # Find all metadata files
        metadata_files = output_dir.glob("*.json")
        
        test_ids = []
        for file in metadata_files:
            data = json.loads(file.read_text())
            test_ids.append(data['id'])
        
        return test_ids
    
    def close(self) -> None:
        """Close the agent and cleanup resources."""
        if self.jira_client:
            self.jira_client.close()
        logger.info("Test Case Agent closed")
