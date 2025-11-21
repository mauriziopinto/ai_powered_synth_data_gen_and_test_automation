"""Workflow orchestration for multi-agent coordination using Strands patterns."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a workflow task."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowState(Enum):
    """State of the workflow."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowTask:
    """Represents a task in the workflow."""
    task_id: str
    description: str
    agent_type: str  # data_processor, synthetic_data, distribution, test_case, test_execution
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'description': self.description,
            'agent_type': self.agent_type,
            'dependencies': self.dependencies,
            'priority': self.priority,
            'status': self.status.value,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


@dataclass
class WorkflowConfig:
    """Configuration for workflow orchestration."""
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    parallel_execution: bool = True
    max_parallel_tasks: int = 3
    checkpoint_enabled: bool = True
    checkpoint_dir: str = "checkpoints"
    state_persistence: bool = True
    state_file: Optional[str] = None
    
    def __post_init__(self):
        if self.state_file is None:
            self.state_file = f"{self.checkpoint_dir}/{self.workflow_id}_state.json"


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflows using Strands patterns."""
    
    def __init__(self, config: WorkflowConfig):
        """Initialize workflow orchestrator.
        
        Args:
            config: Workflow configuration
        """
        self.config = config
        self.state = WorkflowState.CREATED
        self.tasks: Dict[str, WorkflowTask] = {task.task_id: task for task in config.tasks}
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.task_results: Dict[str, Any] = {}
        self.agent_registry: Dict[str, Callable] = {}
        
        # Create checkpoint directory
        if config.checkpoint_enabled:
            Path(config.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized workflow orchestrator: {config.workflow_id}")

    def register_agent(self, agent_type: str, agent_callable: Callable) -> None:
        """Register an agent for execution.
        
        Args:
            agent_type: Type of agent (data_processor, synthetic_data, etc.)
            agent_callable: Callable that executes the agent
        """
        self.agent_registry[agent_type] = agent_callable
        logger.info(f"Registered agent: {agent_type}")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow.
        
        Returns:
            Workflow execution results
        """
        logger.info(f"Starting workflow execution: {self.config.workflow_id}")
        self.state = WorkflowState.RUNNING
        
        try:
            # Load checkpoint if exists
            if self.config.state_persistence:
                self._load_checkpoint()
            
            # Execute tasks
            while not self._is_workflow_complete():
                # Get ready tasks
                ready_tasks = self._get_ready_tasks()
                
                if not ready_tasks:
                    # Check if we're stuck
                    if not self._has_running_tasks():
                        logger.error("Workflow stuck: no ready tasks and no running tasks")
                        self.state = WorkflowState.FAILED
                        break
                    # Wait for running tasks
                    await asyncio.sleep(1)
                    continue
                
                # Execute tasks
                if self.config.parallel_execution:
                    await self._execute_parallel(ready_tasks)
                else:
                    await self._execute_sequential(ready_tasks)
                
                # Save checkpoint
                if self.config.checkpoint_enabled:
                    self._save_checkpoint()
            
            # Determine final state
            if all(task.status == TaskStatus.COMPLETED for task in self.tasks.values()):
                self.state = WorkflowState.COMPLETED
                logger.info("Workflow completed successfully")
            else:
                self.state = WorkflowState.FAILED
                logger.error("Workflow failed")
            
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            self.state = WorkflowState.FAILED
            raise

    def _get_ready_tasks(self) -> List[WorkflowTask]:
        """Get tasks that are ready to execute.
        
        Returns:
            List of ready tasks
        """
        ready_tasks = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_completed = all(
                dep_id in self.completed_tasks 
                for dep_id in task.dependencies
            )
            
            if deps_completed:
                task.status = TaskStatus.READY
                ready_tasks.append(task)
        
        # Sort by priority (higher priority first)
        ready_tasks.sort(key=lambda t: t.priority, reverse=True)
        
        # Limit parallel tasks
        if self.config.parallel_execution:
            ready_tasks = ready_tasks[:self.config.max_parallel_tasks]
        
        return ready_tasks
    
    def _has_running_tasks(self) -> bool:
        """Check if any tasks are currently running."""
        return any(task.status == TaskStatus.RUNNING for task in self.tasks.values())
    
    def _is_workflow_complete(self) -> bool:
        """Check if workflow is complete."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]
            for task in self.tasks.values()
        )
    
    async def _execute_sequential(self, tasks: List[WorkflowTask]) -> None:
        """Execute tasks sequentially."""
        for task in tasks:
            await self._execute_task(task)
    
    async def _execute_parallel(self, tasks: List[WorkflowTask]) -> None:
        """Execute tasks in parallel."""
        await asyncio.gather(*[self._execute_task(task) for task in tasks])

    async def _execute_task(self, task: WorkflowTask) -> None:
        """Execute a single task.
        
        Args:
            task: Task to execute
        """
        logger.info(f"Executing task: {task.task_id}")
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        try:
            # Get agent for this task
            agent = self.agent_registry.get(task.agent_type)
            if not agent:
                raise ValueError(f"No agent registered for type: {task.agent_type}")
            
            # Build context from dependencies
            context = self._build_task_context(task)
            
            # Execute agent
            result = await agent(task.description, context)
            
            # Store result
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            
            self.completed_tasks.append(task.task_id)
            self.task_results[task.task_id] = result
            
            logger.info(f"Task completed: {task.task_id}")
            
        except Exception as e:
            logger.error(f"Task failed: {task.task_id} - {str(e)}")
            task.error = str(e)
            task.retry_count += 1
            
            # Retry logic
            if task.retry_count < task.max_retries:
                logger.info(f"Retrying task: {task.task_id} (attempt {task.retry_count + 1})")
                task.status = TaskStatus.PENDING
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
            else:
                task.status = TaskStatus.FAILED
                task.end_time = datetime.now()
                self.failed_tasks.append(task.task_id)
    
    def _build_task_context(self, task: WorkflowTask) -> Dict[str, Any]:
        """Build context from dependent tasks.
        
        Args:
            task: Task to build context for
        
        Returns:
            Context dictionary
        """
        context = {
            'task_id': task.task_id,
            'workflow_id': self.config.workflow_id,
            'dependencies': {}
        }
        
        # Add results from dependencies
        for dep_id in task.dependencies:
            if dep_id in self.task_results:
                context['dependencies'][dep_id] = self.task_results[dep_id]
        
        return context

    def _save_checkpoint(self) -> None:
        """Save workflow state to checkpoint."""
        if not self.config.state_persistence:
            return
        
        checkpoint = {
            'workflow_id': self.config.workflow_id,
            'state': self.state.value,
            'timestamp': datetime.now().isoformat(),
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'task_results': {k: str(v) for k, v in self.task_results.items()}
        }
        
        checkpoint_file = Path(self.config.state_file)
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.debug(f"Saved checkpoint: {checkpoint_file}")
    
    def _load_checkpoint(self) -> None:
        """Load workflow state from checkpoint."""
        checkpoint_file = Path(self.config.state_file)
        
        if not checkpoint_file.exists():
            logger.debug("No checkpoint found")
            return
        
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            # Restore state
            self.state = WorkflowState(checkpoint['state'])
            self.completed_tasks = checkpoint['completed_tasks']
            self.failed_tasks = checkpoint['failed_tasks']
            
            # Restore task states
            for task_id, task_data in checkpoint['tasks'].items():
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task.status = TaskStatus(task_data['status'])
                    task.retry_count = task_data['retry_count']
                    if task_data['start_time']:
                        task.start_time = datetime.fromisoformat(task_data['start_time'])
                    if task_data['end_time']:
                        task.end_time = datetime.fromisoformat(task_data['end_time'])
                    task.error = task_data['error']
            
            logger.info(f"Loaded checkpoint from: {checkpoint_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {str(e)}")

    def pause(self) -> None:
        """Pause workflow execution."""
        if self.state == WorkflowState.RUNNING:
            self.state = WorkflowState.PAUSED
            self._save_checkpoint()
            logger.info("Workflow paused")
    
    def resume(self) -> None:
        """Resume workflow execution."""
        if self.state == WorkflowState.PAUSED:
            self.state = WorkflowState.RUNNING
            logger.info("Workflow resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status.
        
        Returns:
            Status dictionary
        """
        total_tasks = len(self.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        
        progress = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'workflow_id': self.config.workflow_id,
            'state': self.state.value,
            'progress': progress,
            'total_tasks': total_tasks,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'running_tasks': running,
            'pending_tasks': pending,
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()}
        }
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate workflow execution report.
        
        Returns:
            Execution report
        """
        total_duration = 0
        for task in self.tasks.values():
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                total_duration += duration
        
        return {
            'workflow_id': self.config.workflow_id,
            'name': self.config.name,
            'state': self.state.value,
            'total_tasks': len(self.tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'total_duration': total_duration,
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            'results': self.task_results
        }
    
    def close(self) -> None:
        """Close the orchestrator and cleanup resources."""
        if self.config.checkpoint_enabled:
            self._save_checkpoint()
        logger.info("Workflow orchestrator closed")
