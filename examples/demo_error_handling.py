"""Demo of error handling and retry logic."""

import asyncio
import random
from shared.utils.error_handler import (
    ErrorHandler,
    RetryConfig,
    RetryStrategy,
    ErrorCategory,
    ErrorSeverity,
    ErrorClassifier
)


# Mock functions that simulate different error scenarios
class TransientErrorSimulator:
    """Simulates transient errors that resolve after retries."""
    
    def __init__(self, fail_count: int = 2):
        self.fail_count = fail_count
        self.attempt = 0
    
    async def process_data(self, data: dict) -> dict:
        """Process data with transient failures."""
        self.attempt += 1
        
        if self.attempt <= self.fail_count:
            raise ConnectionError(f"Network timeout - attempt {self.attempt}")
        
        return {
            'status': 'success',
            'records_processed': data.get('record_count', 100),
            'attempts': self.attempt
        }


class DataValidationSimulator:
    """Simulates data validation errors."""
    
    async def validate_data(self, data: dict) -> dict:
        """Validate data with potential errors."""
        if not data.get('required_field'):
            raise ValueError("Missing required field: required_field")
        
        if data.get('value', 0) < 0:
            raise ValueError("Value must be non-negative")
        
        return {'status': 'valid', 'data': data}


class ResourceLimitSimulator:
    """Simulates resource limit errors."""
    
    def __init__(self, fail_probability: float = 0.3):
        self.fail_probability = fail_probability
    
    async def allocate_resources(self, size: int) -> dict:
        """Allocate resources with potential failures."""
        if random.random() < self.fail_probability:
            raise MemoryError("Insufficient memory for allocation")
        
        return {'status': 'allocated', 'size': size}


async def demo_transient_error_retry():
    """Demo transient error handling with retry."""
    print("=" * 80)
    print("TRANSIENT ERROR RETRY DEMO")
    print("=" * 80)
    print("This demo shows automatic retry with exponential backoff for transient errors")
    print("=" * 80)
    print()
    
    # Create error handler with exponential backoff
    retry_config = RetryConfig(
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=3,
        initial_delay=0.5,
        max_delay=10.0,
        backoff_multiplier=2.0,
        jitter=True
    )
    
    error_handler = ErrorHandler(retry_config)
    
    print("📋 Retry Configuration:")
    print(f"   Strategy: {retry_config.strategy.value}")
    print(f"   Max Retries: {retry_config.max_retries}")
    print(f"   Initial Delay: {retry_config.initial_delay}s")
    print(f"   Backoff Multiplier: {retry_config.backoff_multiplier}x")
    print()
    
    # Simulate transient error that resolves after 2 failures
    simulator = TransientErrorSimulator(fail_count=2)
    
    print("🔄 Executing operation with transient failures...")
    print()
    
    try:
        result = await error_handler.execute_with_retry(
            simulator.process_data,
            agent_id="data_processor_001",
            agent_type="DataProcessor",
            operation="process_customer_data",
            data={'record_count': 1000}
        )
        
        print("✅ Operation succeeded!")
        print(f"   Records processed: {result['records_processed']}")
        print(f"   Total attempts: {result['attempts']}")
        print()
        
    except Exception as e:
        print(f"❌ Operation failed: {str(e)}")
        print()
    
    # Show error log
    print("📊 Error Log:")
    for error in error_handler.get_error_log():
        print(f"   • Attempt {error.retry_count + 1}: {error.error_message}")
        print(f"     Category: {error.category.value}")
        print(f"     Severity: {error.severity.value}")
        print(f"     Recoverable: {error.is_recoverable}")
    print()


async def demo_data_validation_error():
    """Demo data validation error handling."""
    print("=" * 80)
    print("DATA VALIDATION ERROR DEMO")
    print("=" * 80)
    print("This demo shows handling of data validation errors")
    print("=" * 80)
    print()
    
    # Create error handler
    retry_config = RetryConfig(
        strategy=RetryStrategy.FIXED_DELAY,
        max_retries=2,
        initial_delay=1.0
    )
    
    error_handler = ErrorHandler(retry_config)
    simulator = DataValidationSimulator()
    
    # Test with invalid data
    print("🔄 Testing with invalid data (missing required field)...")
    print()
    
    try:
        result = await error_handler.execute_with_retry(
            simulator.validate_data,
            agent_id="validator_001",
            agent_type="DataValidator",
            operation="validate_customer_record",
            data={'value': 100}  # Missing required_field
        )
        
        print("✅ Validation succeeded!")
        print()
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        print()
        
        # Get error details
        errors = error_handler.get_error_log()
        if errors:
            latest_error = errors[-1]
            print("📋 Error Details:")
            print(f"   Error ID: {latest_error.error_id}")
            print(f"   Category: {latest_error.category.value}")
            print(f"   Severity: {latest_error.severity.value}")
            print(f"   Recoverable: {latest_error.is_recoverable}")
            print()
            
            print("🔧 Remediation Steps:")
            for i, step in enumerate(latest_error.remediation_steps, 1):
                print(f"   {i}. {step}")
            print()
    
    # Test with valid data
    print("🔄 Testing with valid data...")
    print()
    
    error_handler.clear_error_log()
    
    try:
        result = await error_handler.execute_with_retry(
            simulator.validate_data,
            agent_id="validator_001",
            agent_type="DataValidator",
            operation="validate_customer_record",
            data={'required_field': 'value', 'value': 100}
        )
        
        print("✅ Validation succeeded!")
        print(f"   Status: {result['status']}")
        print()
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        print()


async def demo_error_classification():
    """Demo error classification system."""
    print("=" * 80)
    print("ERROR CLASSIFICATION DEMO")
    print("=" * 80)
    print("This demo shows automatic error classification")
    print("=" * 80)
    print()
    
    classifier = ErrorClassifier()
    
    # Test different error types
    test_errors = [
        (ConnectionError("Connection timeout"), "Connection Error"),
        (ValueError("Invalid data format"), "Value Error"),
        (PermissionError("Access denied"), "Permission Error"),
        (MemoryError("Out of memory"), "Memory Error"),
        (TimeoutError("Request timeout"), "Timeout Error"),
        (Exception("Unknown error occurred"), "Generic Exception")
    ]
    
    print("📊 Error Classification Results:")
    print()
    
    for error, description in test_errors:
        category = classifier.classify(error)
        severity = classifier.determine_severity(category, error)
        is_recoverable = classifier.is_recoverable(category)
        
        print(f"   {description}:")
        print(f"      Category: {category.value}")
        print(f"      Severity: {severity.value}")
        print(f"      Recoverable: {'Yes' if is_recoverable else 'No'}")
        print()


async def demo_remediation_steps():
    """Demo remediation step generation."""
    print("=" * 80)
    print("REMEDIATION STEPS DEMO")
    print("=" * 80)
    print("This demo shows automatic generation of remediation steps")
    print("=" * 80)
    print()
    
    from shared.utils.error_handler import ErrorContext, RemediationStepGenerator
    from datetime import datetime
    
    generator = RemediationStepGenerator()
    
    # Test different error categories
    test_cases = [
        (ErrorCategory.TRANSIENT, "Network timeout"),
        (ErrorCategory.CONFIGURATION, "Invalid configuration parameter"),
        (ErrorCategory.DATA, "Data validation failed"),
        (ErrorCategory.RESOURCE, "Insufficient memory"),
        (ErrorCategory.PERMISSION, "Access denied")
    ]
    
    print("🔧 Remediation Steps by Error Category:")
    print()
    
    for category, error_msg in test_cases:
        error_context = ErrorContext(
            error_id="test_001",
            timestamp=datetime.now(),
            agent_id="test_agent",
            agent_type="TestAgent",
            operation="test_operation",
            error_type="TestError",
            error_message=error_msg,
            stack_trace="",
            category=category,
            severity=ErrorSeverity.MEDIUM
        )
        
        steps = generator.generate_steps(error_context)
        
        print(f"   {category.value.upper()} - {error_msg}:")
        for i, step in enumerate(steps, 1):
            print(f"      {i}. {step}")
        print()


async def demo_error_log_export():
    """Demo error log export functionality."""
    print("=" * 80)
    print("ERROR LOG EXPORT DEMO")
    print("=" * 80)
    print("This demo shows error logging and export")
    print("=" * 80)
    print()
    
    # Create error handler and generate some errors
    error_handler = ErrorHandler()
    
    # Simulate multiple operations with errors
    simulators = [
        TransientErrorSimulator(fail_count=1),
        DataValidationSimulator(),
        ResourceLimitSimulator(fail_probability=1.0)
    ]
    
    print("🔄 Generating error log entries...")
    print()
    
    # Execute operations
    for i, simulator in enumerate(simulators):
        try:
            if isinstance(simulator, TransientErrorSimulator):
                await error_handler.execute_with_retry(
                    simulator.process_data,
                    agent_id=f"agent_{i}",
                    agent_type="DataProcessor",
                    operation="process_data",
                    data={'record_count': 100}
                )
            elif isinstance(simulator, DataValidationSimulator):
                await error_handler.execute_with_retry(
                    simulator.validate_data,
                    agent_id=f"agent_{i}",
                    agent_type="Validator",
                    operation="validate_data",
                    data={}  # Invalid data
                )
            else:
                await error_handler.execute_with_retry(
                    simulator.allocate_resources,
                    agent_id=f"agent_{i}",
                    agent_type="ResourceManager",
                    operation="allocate_resources",
                    size=1000
                )
        except Exception:
            pass  # Expected failures
    
    # Show error statistics
    print("📊 Error Log Statistics:")
    print(f"   Total Errors: {len(error_handler.get_error_log())}")
    print()
    
    # Show errors by category
    print("📋 Errors by Category:")
    for category in ErrorCategory:
        errors = error_handler.get_errors_by_category(category)
        if errors:
            print(f"   {category.value}: {len(errors)}")
    print()
    
    # Show errors by severity
    print("📋 Errors by Severity:")
    for severity in ErrorSeverity:
        errors = error_handler.get_errors_by_severity(severity)
        if errors:
            print(f"   {severity.value}: {len(errors)}")
    print()
    
    # Export error log
    output_file = "error_log_demo.json"
    error_handler.export_error_log(output_file)
    print(f"✅ Error log exported to {output_file}")
    print()


async def main():
    """Run all error handling demos."""
    print("\n")
    print("=" * 80)
    print("ERROR HANDLING & RETRY LOGIC DEMO")
    print("=" * 80)
    print("This demo showcases comprehensive error handling features:")
    print("  • Automatic retry with exponential backoff")
    print("  • Error classification and categorization")
    print("  • Severity assessment")
    print("  • Remediation step generation")
    print("  • Error logging and export")
    print("  • Workflow pause and recovery")
    print("=" * 80)
    print("\n")
    
    # Run demos
    await demo_transient_error_retry()
    await demo_data_validation_error()
    await demo_error_classification()
    await demo_remediation_steps()
    await demo_error_log_export()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(main())
