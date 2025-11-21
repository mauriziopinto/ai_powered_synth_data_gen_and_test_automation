"""Confluence client for retrieving documentation and field definitions."""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ConfluenceSearchResult:
    """Result from a Confluence search."""
    page_id: str
    title: str
    content: str
    url: str
    space: str
    excerpt: str = ""


class ConfluenceClient(ABC):
    """Abstract base class for Confluence clients."""
    
    @abstractmethod
    async def search(self, query: str, space: Optional[str] = None, limit: int = 5) -> List[ConfluenceSearchResult]:
        """Search Confluence for documentation.
        
        Args:
            query: Search query string
            space: Optional space key to limit search
            limit: Maximum number of results to return
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def get_page(self, page_id: str) -> ConfluenceSearchResult:
        """Get a specific Confluence page by ID.
        
        Args:
            page_id: Page ID to retrieve
            
        Returns:
            Page content
        """
        pass


class MockConfluenceClient(ConfluenceClient):
    """Mock Confluence client for demo mode."""
    
    def __init__(self):
        """Initialize mock client with pre-configured documentation."""
        self.mock_data = {
            'email': {
                'title': 'Email Field Standards',
                'content': '''
                # Email Field Standards
                
                ## Overview
                Email fields contain customer email addresses and are classified as Personally Identifiable Information (PII).
                
                ## Data Classification
                - **Sensitivity Level**: High
                - **GDPR Category**: Personal Data
                - **Retention Policy**: 7 years after last contact
                
                ## Field Naming Conventions
                - email
                - email_address
                - customer_email
                - contact_email
                
                ## Validation Rules
                - Must follow RFC 5322 format
                - Domain must be valid and resolvable
                - Maximum length: 254 characters
                
                ## Synthetic Data Generation
                For testing purposes, use synthetic email addresses that:
                - Follow valid email format
                - Use test domains (example.com, test.org)
                - Do not match any real customer emails
                ''',
                'space': 'DATA',
                'excerpt': 'Email fields contain customer email addresses and are classified as PII.'
            },
            'phone': {
                'title': 'Phone Number Field Standards',
                'content': '''
                # Phone Number Field Standards
                
                ## Overview
                Phone number fields store customer contact numbers and are classified as PII.
                
                ## Data Classification
                - **Sensitivity Level**: High
                - **GDPR Category**: Personal Data
                - **Retention Policy**: 7 years after last contact
                
                ## Field Naming Conventions
                - phone
                - phone_number
                - mobile
                - telephone
                - contact_number
                
                ## Format Standards
                - US: (XXX) XXX-XXXX or XXX-XXX-XXXX
                - International: +XX XXX XXX XXXX
                - Store with country code when available
                
                ## Synthetic Data Generation
                Use synthetic phone numbers that:
                - Follow valid format patterns
                - Use reserved test ranges (555-0100 to 555-0199 in US)
                - Do not match real customer numbers
                ''',
                'space': 'DATA',
                'excerpt': 'Phone number fields store customer contact numbers and are classified as PII.'
            },
            'name': {
                'title': 'Name Field Standards',
                'content': '''
                # Name Field Standards
                
                ## Overview
                Name fields (first name, last name, full name) contain customer identity information and are classified as PII.
                
                ## Data Classification
                - **Sensitivity Level**: High
                - **GDPR Category**: Personal Data
                - **Retention Policy**: 7 years after account closure
                
                ## Field Naming Conventions
                - first_name, firstname, given_name
                - last_name, lastname, surname, family_name
                - full_name, name, customer_name
                
                ## Data Quality Standards
                - Proper capitalization
                - Support for international characters (UTF-8)
                - Handle hyphenated names, prefixes, suffixes
                
                ## Synthetic Data Generation
                Use synthetic names that:
                - Represent diverse cultural backgrounds
                - Follow realistic naming patterns
                - Do not match real customer names
                ''',
                'space': 'DATA',
                'excerpt': 'Name fields contain customer identity information and are classified as PII.'
            },
            'address': {
                'title': 'Address Field Standards',
                'content': '''
                # Address Field Standards
                
                ## Overview
                Address fields contain customer location information and are classified as PII.
                
                ## Data Classification
                - **Sensitivity Level**: High
                - **GDPR Category**: Personal Data
                - **Retention Policy**: 7 years after last transaction
                
                ## Field Naming Conventions
                - address, street_address, address_line1
                - city, town
                - state, province, region
                - postal_code, zip_code, postcode
                - country
                
                ## Format Standards
                - Follow local postal standards
                - Support international addresses
                - Validate postal codes against country formats
                
                ## Synthetic Data Generation
                Use synthetic addresses that:
                - Follow valid postal formats
                - Use realistic street names and numbers
                - Do not match real customer addresses
                ''',
                'space': 'DATA',
                'excerpt': 'Address fields contain customer location information and are classified as PII.'
            },
            'ssn': {
                'title': 'Social Security Number Field Standards',
                'content': '''
                # Social Security Number Field Standards
                
                ## Overview
                SSN fields contain highly sensitive government-issued identifiers.
                
                ## Data Classification
                - **Sensitivity Level**: Critical
                - **GDPR Category**: Special Category Personal Data
                - **Retention Policy**: Minimum required by law
                
                ## Field Naming Conventions
                - ssn
                - social_security_number
                - national_id
                - tax_id
                
                ## Security Requirements
                - Must be encrypted at rest
                - Access logging required
                - Limited to authorized personnel only
                
                ## Synthetic Data Generation
                Use synthetic SSNs that:
                - Follow XXX-XX-XXXX format
                - Use invalid ranges (000, 666, 900-999 for first group)
                - Never use real SSNs
                ''',
                'space': 'DATA',
                'excerpt': 'SSN fields contain highly sensitive government-issued identifiers.'
            },
            'account': {
                'title': 'Account Number Field Standards',
                'content': '''
                # Account Number Field Standards
                
                ## Overview
                Account numbers are unique identifiers for customer accounts.
                
                ## Data Classification
                - **Sensitivity Level**: Medium
                - **GDPR Category**: May be Personal Data depending on context
                - **Retention Policy**: Indefinite for audit purposes
                
                ## Field Naming Conventions
                - account_number
                - account_id
                - customer_id
                - customer_account
                
                ## Format Standards
                - Typically numeric or alphanumeric
                - May include check digits
                - Length varies by system (8-20 characters common)
                
                ## Synthetic Data Generation
                Use synthetic account numbers that:
                - Follow the same format as production
                - Maintain uniqueness
                - Use reserved ranges for testing
                ''',
                'space': 'DATA',
                'excerpt': 'Account numbers are unique identifiers for customer accounts.'
            },
            'payment': {
                'title': 'Payment Information Field Standards',
                'content': '''
                # Payment Information Field Standards
                
                ## Overview
                Payment fields include credit card numbers, bank accounts, and payment methods.
                
                ## Data Classification
                - **Sensitivity Level**: Critical
                - **PCI-DSS**: Cardholder Data
                - **Retention Policy**: Minimum required, tokenize when possible
                
                ## Field Naming Conventions
                - credit_card, cc_number, card_number
                - bank_account, account_number
                - payment_method, payment_type
                
                ## Security Requirements
                - PCI-DSS compliance mandatory
                - Encryption required
                - Tokenization recommended
                - Never log or display full numbers
                
                ## Synthetic Data Generation
                Use synthetic payment data that:
                - Follows Luhn algorithm for credit cards
                - Uses test card numbers (4111111111111111)
                - Never uses real payment information
                ''',
                'space': 'DATA',
                'excerpt': 'Payment fields include credit card numbers and are subject to PCI-DSS.'
            },
        }
    
    async def search(self, query: str, space: Optional[str] = None, limit: int = 5) -> List[ConfluenceSearchResult]:
        """Search mock Confluence data.
        
        Simulates search latency and returns relevant mock documentation.
        """
        # Simulate network latency
        await self._simulate_latency(0.5)
        
        results = []
        query_lower = query.lower()
        
        # Search through mock data
        for key, data in self.mock_data.items():
            # Check if query matches key or content
            if (key in query_lower or 
                query_lower in data['title'].lower() or 
                query_lower in data['content'].lower()):
                
                # Filter by space if specified
                if space and data['space'] != space:
                    continue
                
                results.append(ConfluenceSearchResult(
                    page_id=f'mock-{key}-001',
                    title=data['title'],
                    content=data['content'],
                    url=f'https://confluence.example.com/display/{data["space"]}/{key}',
                    space=data['space'],
                    excerpt=data['excerpt']
                ))
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_page(self, page_id: str) -> ConfluenceSearchResult:
        """Get a specific mock page."""
        # Simulate network latency
        await self._simulate_latency(0.3)
        
        # Extract key from page_id (format: mock-{key}-001)
        if page_id.startswith('mock-'):
            key = page_id.split('-')[1]
            if key in self.mock_data:
                data = self.mock_data[key]
                return ConfluenceSearchResult(
                    page_id=page_id,
                    title=data['title'],
                    content=data['content'],
                    url=f'https://confluence.example.com/display/{data["space"]}/{key}',
                    space=data['space'],
                    excerpt=data['excerpt']
                )
        
        raise ValueError(f'Page not found: {page_id}')
    
    async def _simulate_latency(self, seconds: float):
        """Simulate network latency for realistic demo."""
        # In async context, we would use asyncio.sleep
        # For now, using time.sleep for simplicity
        time.sleep(seconds)


class RealConfluenceClient(ConfluenceClient):
    """Real Confluence client using Atlassian API."""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        """Initialize real Confluence client.
        
        Args:
            base_url: Confluence instance URL (e.g., https://company.atlassian.net/wiki)
            username: Confluence username/email
            api_token: API token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = None
    
    async def search(self, query: str, space: Optional[str] = None, limit: int = 5) -> List[ConfluenceSearchResult]:
        """Search Confluence using CQL (Confluence Query Language).
        
        Note: This is a placeholder implementation. In production, you would use
        the atlassian-python-api library or make direct REST API calls.
        """
        # TODO: Implement real Confluence API integration
        # This would use the Confluence REST API:
        # GET /rest/api/content/search?cql=text~"{query}"
        
        raise NotImplementedError(
            'Real Confluence integration requires atlassian-python-api library. '
            'Use MockConfluenceClient for demo mode.'
        )
    
    async def get_page(self, page_id: str) -> ConfluenceSearchResult:
        """Get a specific Confluence page.
        
        Note: This is a placeholder implementation.
        """
        # TODO: Implement real Confluence API integration
        # This would use the Confluence REST API:
        # GET /rest/api/content/{page_id}?expand=body.storage
        
        raise NotImplementedError(
            'Real Confluence integration requires atlassian-python-api library. '
            'Use MockConfluenceClient for demo mode.'
        )


def create_confluence_client(demo_mode: bool = True, 
                            base_url: Optional[str] = None,
                            username: Optional[str] = None,
                            api_token: Optional[str] = None) -> ConfluenceClient:
    """Factory function to create appropriate Confluence client.
    
    Args:
        demo_mode: If True, return mock client. If False, return real client.
        base_url: Confluence instance URL (required for real client)
        username: Confluence username (required for real client)
        api_token: API token (required for real client)
        
    Returns:
        ConfluenceClient instance (mock or real)
    """
    if demo_mode:
        return MockConfluenceClient()
    else:
        if not all([base_url, username, api_token]):
            raise ValueError(
                'Real Confluence client requires base_url, username, and api_token'
            )
        return RealConfluenceClient(base_url, username, api_token)
