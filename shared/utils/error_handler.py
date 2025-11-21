"""Error handling and retry logic for workflow execution."""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    TRANSIENT = "transient"  # Temporary errors that may resolve with retry
    CONFIGURATION = "configuration"  # Configuration or setup errors
    DATA = "data"  # Data validation or processing errors
    RESOURCE = "resource"  # Resource availability errors
    PERMISSION = "permission"  # Authorization or permission errors
    SYSTEM = "system"  # System or infrastructure errors
    UNKNOWN = "unknown"  # Unclassified errors


class RetryStrategy(Enum):
    """Retry strategies."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    NO_RETRY = "no_retry"


@dataclass
class ErrorContext:
    """Context information for an error."""
    error_id: str
    timestamp: datetime
    agent_id: str
    agent_type: str
    operation: str
    error_type: str
    error_message: str
    stack_trace: str
    category: ErrorCategory
    severity: ErrorSeverity
    affected_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    is_recoverable: bool = True
    remediation_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'operation': self.operation,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'category': self.category.value,
            'severity': self.severity.value,
            'affected_data': self.affected_data,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'is_recoverable': self.is_recoverable,
            'remediation_steps': self.remediation_steps,
            'metadata': self.metadata
        }


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd
    retry_on_exceptions: List[Type[Exception]] = field(default_factory=list)
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay for retry attempt.
        
        Args:
            retry_count: Current retry attempt number
        
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.NO_RETRY:
            return 0.0
        
        if self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.initial_delay * (retry_count + 1)
        else:  # EXPONENTIAL_BACKOFF
            delay = self.initial_delay * (self.backoff_multiplier ** retry_count)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay


class ErrorClassifier:
    """Classifies errors into categories and determines handling strategy."""
    
    # Transient error patterns
    TRANSIENT_PATTERNS = [
        'timeout', 'connection', 'network', 'temporary', 'unavailable',
        'throttle', 'rate limit', 'too many requests', 'service unavailable'
    ]
    
    # Configuration error patterns
    CONFIG_PATTERNS = [
        'configuration', 'config', 'invalid parameter', 'missing parameter',
        'not configured', 'setup', 'initialization'
    ]
    
    # Data error patterns
    DATA_PATTERNS = [
        'validation', 'invalid data', 'parse', 'format', 'schema',
        'constraint', 'integrity', 'malformed'
    ]
    
    # Resource error patterns
    RESOURCE_PATTERNS = [
        'memory', 'disk', 'quota', 'limit exceeded', 'capacity',
        'resource', 'out of'
    ]
    
    # Permission error patterns
    PERMISSION_PATTERNS = [
        'permission', 'unauthorized', 'forbidden', 'access denied',
        'authentication', 'credential'
    ]
    
    @classmethod
    def classify(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorCategory:
        """Classify an error into a category.
        
        Args:
            error: Exception to classify
            context: Optional context information
        
        Returns:
            Error category
        """
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check for transient errors
        if any(pattern in error_msg or pattern in error_type for pattern in cls.TRANSIENT_PATTERNS):
            return ErrorCategory.TRANSIENT
        
        # Check for configuration errors
        if any(pattern in error_msg or pattern in error_type for pattern in cls.CONFIG_PATTERNS):
            return ErrorCategory.CONFIGURATION
        
        # Check for data errors
        if any(pattern in error_msg or pattern in error_type for pattern in cls.DATA_PATTERNS):
            return ErrorCategory.DATA
        
        # Check for resource errors
        if any(pattern in error_msg or pattern in error_type for pattern in cls.RESOURCE_PATTERNS):
            return ErrorCategory.RESOURCE
        
        # Check for permission errors
        if any(pattern in error_msg or pattern in error_type for pattern in cls.PERMISSION_PATTERNS):
            return ErrorCategory.PERMISSION
        
        # Check specific exception types
        if isinstance(error, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
            return ErrorCategory.TRANSIENT
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.DATA
        elif isinstance(error, PermissionError):
            return ErrorCategory.PERMISSION
        elif isinstance(error, (MemoryError, OSError)):
            return ErrorCategory.RESOURCE
        
        return ErrorCategory.UNKNOWN
    
    @classmethod
    def determine_severity(cls, category: ErrorCategory, error: Exception) -> ErrorSeverity:
        """Determine error severity.
        
        Args:
            category: Error category
            error: Exception
        
        Returns:
            Error severity
        """
        # Critical errors
        if isinstance(error, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        
        # High severity
        if category in [ErrorCategory.PERMISSION, ErrorCategory.SYSTEM]:
            return ErrorSeverity.HIGH
        
        # Medium severity
        if category in [ErrorCategory.CONFIGURATION, ErrorCategory.RESOURCE]:
            return ErrorSeverity.MEDIUM
        
        # Low severity (transient, data errors)
        return ErrorSeverity.LOW
    
    @classmethod
    def is_recoverable(cls, category: ErrorCategory) -> bool:
        """Determine if error is recoverable.
        
        Args:
            category: Error category
        
        Returns:
            True if error is recoverable
        """
        # Transient errors are usually recoverable
        if category == ErrorCategory.TRANSIENT:
            return True
        
        # Data errors may be recoverable with different input
        if category == ErrorCategory.DATA:
            return True
        
        # Configuration and permission errors usually require manual intervention
        if category in [ErrorCategory.CONFIGURATION, ErrorCategory.PERMISSION]:
            return False
        
        # Resource errors may be recoverable after waiting
        if category == ErrorCategory.RESOURCE:
            return True
        
        return False


class RemediationStepGenerator:
    """Generates remediation steps for different error types."""
    
    @classmethod
    def generate_steps(cls, error_context: ErrorContext) -> List[str]:
        """Generate remediation steps based on error context.
        
        Args:
            error_context: Error context information
        
        Returns:
            List of remediation steps
        """
        steps = []
        
        if error_context.category == ErrorCategory.TRANSIENT:
            steps.extend([
                "Wait a few moments and retry the operation",
                "Check network connectivity",
                "Verify that external services are available",
                f"The system will automatically retry up to {error_context.max_retries} times"
            ])
        
        elif error_context.category == ErrorCategory.CONFIGURATION:
            steps.extend([
                "Review configuration settings",
                "Verify all required parameters are provided",
                "Check configuration file format and syntax",
                "Consult documentation for correct configuration values"
            ])
        
        elif error_context.category == ErrorCategory.DATA:
            steps.extend([
                "Validate input data format and structure",
                "Check for missing or malformed data fields",
                "Review data constraints and requirements",
                "Consider using data validation tools before processing"
            ])
        
        elif error_context.category == ErrorCategory.RESOURCE:
            steps.extend([
                "Check available system resources (memory, disk space)",
                "Consider reducing batch size or data volume",
                "Close unnecessary applications or processes",
                "Wait for resources to become available and retry"
            ])
        
        elif error_context.category == ErrorCategory.PERMISSION:
            steps.extend([
                "Verify authentication credentials",
                "Check user permissions and access rights",
                "Contact system administrator for access",
                "Review security policies and requirements"
            ])
        
        elif error_context.category == ErrorCategory.SYSTEM:
            steps.extend([
                "Check system logs for additional details",
                "Verify system dependencies are installed",
                "Restart the application or service",
                "Contact technical support if issue persists"
            ])
        
        else:  # UNKNOWN
            steps.extend([
                "Review error message and stack trace",
                "Check application logs for more details",
                "Try the operation again",
                "Contact support with error details if issue persists"
            ])
        
        # Add specific steps based on error message
        error_msg_lower = error_context.error_message.lower()
        
        if 'api' in error_msg_lower or 'endpoint' in error_msg_lower:
            steps.append("Verify API endpoint URL and credentials")
        
        if 'file' in error_msg_lower or 'path' in error_msg_lower:
            steps.append("Check file path and ensure file exists")
        
        if 'database' in error_msg_lower or 'connection' in error_msg_lower:
            steps.append("Verify database connection settings")
        
        return steps


class ErrorHandler:
    """Handles errors with retry logic and recovery mechanisms."""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """Initialize error handler.
        
        Args:
            retry_config: Retry configuration
        """
        self.retry_config = retry_config or RetryConfig()
        self.error_log: List[ErrorContext] = []
        self.classifier = ErrorClassifier()
        self.remediation_generator = RemediationStepGenerator()
    
    async def execute_with_retry(
        self,
        func: Callable,
        agent_id: str,
        agent_type: str,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            agent_id: Agent identifier
            agent_type: Agent type
            operation: Operation name
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success - log if this was a retry
                if attempt > 0:
                    logger.info(f"Operation {operation} succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Classify error
                category = self.classifier.classify(e)
                severity = self.classifier.determine_severity(category, e)
                is_recoverable = self.classifier.is_recoverable(category)
                
                # Check if we should retry
                should_retry = (
                    attempt < self.retry_config.max_retries and
                    is_recoverable and
                    (not self.retry_config.retry_on_exceptions or 
                     type(e) in self.retry_config.retry_on_exceptions)
                )
                
                # Create error context
                error_context = ErrorContext(
                    error_id=f"{agent_id}_{operation}_{int(time.time())}",
                    timestamp=datetime.now(),
                    agent_id=agent_id,
                    agent_type=agent_type,
                    operation=operation,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    category=category,
                    severity=severity,
                    retry_count=attempt,
                    max_retries=self.retry_config.max_retries,
                    is_recoverable=is_recoverable
                )
                
                # Generate remediation steps
                error_context.remediation_steps = self.remediation_generator.generate_steps(error_context)
                
                # Log error
                self.error_log.append(error_context)
                
                if should_retry:
                    # Calculate delay
                    delay = self.retry_config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Operation {operation} failed (attempt {attempt + 1}/{self.retry_config.max_retries + 1}): "
                        f"{str(e)}. Retrying in {delay:.2f}s..."
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                else:
                    # No more retries or not recoverable
                    logger.error(
                        f"Operation {operation} failed after {attempt + 1} attempts: {str(e)}"
                    )
                    raise
        
        # Should not reach here, but raise last error if we do
        if last_error:
            raise last_error
    
    def get_error_log(self) -> List[ErrorContext]:
        """Get error log.
        
        Returns:
            List of error contexts
        """
        return self.error_log
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorContext]:
        """Get errors by category.
        
        Args:
            category: Error category
        
        Returns:
            List of error contexts
        """
        return [e for e in self.error_log if e.category == category]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorContext]:
        """Get errors by severity.
        
        Args:
            severity: Error severity
        
        Returns:
            List of error contexts
        """
        return [e for e in self.error_log if e.severity == severity]
    
    def get_recent_errors(self, count: int = 10) -> List[ErrorContext]:
        """Get most recent errors.
        
        Args:
            count: Number of errors to return
        
        Returns:
            List of error contexts
        """
        return sorted(self.error_log, key=lambda e: e.timestamp, reverse=True)[:count]
    
    def clear_error_log(self) -> None:
        """Clear error log."""
        self.error_log.clear()
    
    def export_error_log(self, filepath: str) -> None:
        """Export error log to file.
        
        Args:
            filepath: Output file path
        """
        import json
        
        with open(filepath, 'w') as f:
            json.dump(
                [e.to_dict() for e in self.error_log],
                f,
                indent=2
            )
        
        logger.info(f"Exported {len(self.error_log)} errors to {filepath}")
