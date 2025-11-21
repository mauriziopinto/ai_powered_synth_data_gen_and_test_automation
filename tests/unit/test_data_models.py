"""Tests for data model serialization/deserialization."""

import pytest
from datetime import datetime
from pathlib import Path
import pandas as pd

from shared.models.workflow import (
    WorkflowConfig, WorkflowExecution, WorkflowStatus, TargetConfig
)
from shared.models.sensitivity import FieldClassification, SensitivityReport
from shared.models.quality import QualityMetrics, SyntheticDataset
from shared.models.test_results import TestResult, TestResults


class TestWorkflowConfigSerialization:
    """Test WorkflowConfig serialization/deserialization."""
    
    def test_workflow_config_to_dict(self):
        """Test converting WorkflowConfig to dictionary."""
        config = WorkflowConfig(
            id='test-id',
            name='Test Config',
            description='Test description',
            created_by='test_user',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            production_data_path=Path('/data/test.csv'),
            sdv_model='gaussian_copula',
            num_synthetic_records=1000
        )
        
        data = config.to_dict()
        
        assert data['id'] == 'test-id'
        assert data['name'] == 'Test Config'
        assert data['production_data_path'] == '/data/test.csv'
        assert data['created_at'] == '2024-01-01T12:00:00'
    
    def test_workflow_config_from_dict(self):
        """Test creating WorkflowConfig from dictionary."""
        data = {
            'id': 'test-id',
            'name': 'Test Config',
            'description': 'Test description',
            'created_by': 'test_user',
            'created_at': '2024-01-01T12:00:00',
            'production_data_path': '/data/test.csv',
            'sdv_model': 'gaussian_copula',
            'num_synthetic_records': 1000,
            'targets': []
        }
        
        config = WorkflowConfig.from_dict(data)
        
        assert config.id == 'test-id'
        assert config.name == 'Test Config'
        assert isinstance(config.production_data_path, Path)
        assert isinstance(config.created_at, datetime)
    
    def test_workflow_config_json_round_trip(self):
        """Test JSON serialization round trip."""
        original = WorkflowConfig(
            id='test-id',
            name='Test Config',
            description='Test description',
            created_by='test_user',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            production_data_path=Path('/data/test.csv'),
            tags=['test', 'demo']
        )
        
        json_str = original.to_json()
        restored = WorkflowConfig.from_json(json_str)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.tags == original.tags


class TestTargetConfigSerialization:
    """Test TargetConfig serialization/deserialization."""
    
    def test_target_config_round_trip(self):
        """Test TargetConfig serialization round trip."""
        original = TargetConfig(
            name='test-db',
            type='database',
            connection_string='postgresql://localhost/test',
            load_strategy='upsert'
        )
        
        data = original.to_dict()
        restored = TargetConfig.from_dict(data)
        
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.connection_string == original.connection_string


class TestWorkflowExecutionSerialization:
    """Test WorkflowExecution serialization/deserialization."""
    
    def test_workflow_execution_to_dict(self):
        """Test converting WorkflowExecution to dictionary."""
        execution = WorkflowExecution(
            id='exec-id',
            config_id='config-id',
            status=WorkflowStatus.RUNNING,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            current_agent='data_processor'
        )
        
        data = execution.to_dict()
        
        assert data['id'] == 'exec-id'
        assert data['status'] == 'running'
        assert data['current_agent'] == 'data_processor'
    
    def test_workflow_execution_from_dict(self):
        """Test creating WorkflowExecution from dictionary."""
        data = {
            'id': 'exec-id',
            'config_id': 'config-id',
            'status': 'running',
            'started_at': '2024-01-01T12:00:00',
            'current_agent': 'data_processor'
        }
        
        execution = WorkflowExecution.from_dict(data)
        
        assert execution.id == 'exec-id'
        assert execution.status == WorkflowStatus.RUNNING
        assert isinstance(execution.started_at, datetime)


class TestSensitivityReportSerialization:
    """Test SensitivityReport serialization/deserialization."""
    
    def test_field_classification_round_trip(self):
        """Test FieldClassification serialization round trip."""
        original = FieldClassification(
            field_name='email',
            is_sensitive=True,
            sensitivity_type='email',
            confidence=0.95,
            reasoning='Pattern match',
            recommended_strategy='bedrock_generation',
            pattern_matches=['email_pattern']
        )
        
        data = original.to_dict()
        restored = FieldClassification.from_dict(data)
        
        assert restored.field_name == original.field_name
        assert restored.is_sensitive == original.is_sensitive
        assert restored.confidence == original.confidence
    
    def test_sensitivity_report_json_round_trip(self):
        """Test SensitivityReport JSON serialization round trip."""
        classification = FieldClassification(
            field_name='email',
            is_sensitive=True,
            sensitivity_type='email',
            confidence=0.95,
            reasoning='Pattern match',
            recommended_strategy='bedrock_generation'
        )
        
        original = SensitivityReport(
            classifications={'email': classification},
            data_profile={'email': {'dtype': 'object'}},
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            total_fields=1,
            sensitive_fields=1,
            confidence_distribution={'high': 1}
        )
        
        json_str = original.to_json()
        restored = SensitivityReport.from_json(json_str)
        
        assert len(restored.classifications) == 1
        assert 'email' in restored.classifications
        assert restored.total_fields == 1


class TestQualityMetricsSerialization:
    """Test QualityMetrics serialization/deserialization."""
    
    def test_quality_metrics_json_round_trip(self):
        """Test QualityMetrics JSON serialization round trip."""
        original = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={'age': {'statistic': 0.1, 'pvalue': 0.5}},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92
        )
        
        json_str = original.to_json()
        restored = QualityMetrics.from_json(json_str)
        
        assert restored.sdv_quality_score == original.sdv_quality_score
        assert restored.correlation_preservation == original.correlation_preservation


class TestSyntheticDatasetSerialization:
    """Test SyntheticDataset serialization/deserialization."""
    
    def test_synthetic_dataset_to_dict_without_data(self):
        """Test converting SyntheticDataset to dictionary without data."""
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        metrics = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92
        )
        
        dataset = SyntheticDataset(
            data=df,
            quality_metrics=metrics,
            generation_metadata={'model': 'gaussian_copula'},
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            seed=42
        )
        
        data = dataset.to_dict(include_data=False)
        
        assert 'data' not in data
        assert data['num_records'] == 3
        assert data['seed'] == 42
    
    def test_synthetic_dataset_to_dict_with_data(self):
        """Test converting SyntheticDataset to dictionary with data."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        metrics = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92
        )
        
        dataset = SyntheticDataset(
            data=df,
            quality_metrics=metrics,
            generation_metadata={'model': 'gaussian_copula'},
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        data = dataset.to_dict(include_data=True)
        
        assert 'data' in data
        assert len(data['data']) == 2


class TestTestResultsSerialization:
    """Test TestResults serialization/deserialization."""
    
    def test_test_result_json_round_trip(self):
        """Test TestResult JSON serialization round trip."""
        original = TestResult(
            test_id='test-1',
            test_name='Test Login',
            status='passed',
            duration=1.5,
            logs='Test passed successfully',
            screenshots=[b'fake_screenshot_data']
        )
        
        json_str = original.to_json()
        restored = TestResult.from_json(json_str)
        
        assert restored.test_id == original.test_id
        assert restored.status == original.status
        assert len(restored.screenshots) == 1
    
    def test_test_results_json_round_trip(self):
        """Test TestResults JSON serialization round trip."""
        result1 = TestResult(
            test_id='test-1',
            test_name='Test 1',
            status='passed',
            duration=1.0,
            logs='Passed'
        )
        result2 = TestResult(
            test_id='test-2',
            test_name='Test 2',
            status='failed',
            duration=2.0,
            logs='Failed',
            error='Assertion error'
        )
        
        original = TestResults(
            total=2,
            passed=1,
            failed=1,
            results=[result1, result2]
        )
        
        json_str = original.to_json()
        restored = TestResults.from_json(json_str)
        
        assert restored.total == 2
        assert restored.passed == 1
        assert len(restored.results) == 2
        assert restored.pass_rate == 50.0


# ============================================================================
# Data Model Validation Tests
# ============================================================================

class TestWorkflowConfigValidation:
    """Test WorkflowConfig validation logic."""
    
    def test_workflow_config_requires_id(self):
        """Test that WorkflowConfig requires an id."""
        with pytest.raises(TypeError):
            WorkflowConfig(
                name='Test',
                description='Test',
                created_by='user',
                created_at=datetime.now(),
                production_data_path=Path('/data/test.csv')
            )
    
    def test_workflow_config_default_values(self):
        """Test WorkflowConfig default values."""
        config = WorkflowConfig(
            id='test-id',
            name='Test',
            description='Test',
            created_by='user',
            created_at=datetime.now(),
            production_data_path=Path('/data/test.csv')
        )
        
        assert config.sdv_model == 'gaussian_copula'
        assert config.num_synthetic_records == 1000
        assert config.preserve_edge_cases is True
        assert config.edge_case_frequency == 0.05
        assert config.targets == []
        assert config.tags == []
    
    def test_workflow_config_with_targets(self):
        """Test WorkflowConfig with target configurations."""
        target = TargetConfig(
            name='test-db',
            type='database',
            connection_string='postgresql://localhost/test'
        )
        
        config = WorkflowConfig(
            id='test-id',
            name='Test',
            description='Test',
            created_by='user',
            created_at=datetime.now(),
            production_data_path=Path('/data/test.csv'),
            targets=[target]
        )
        
        assert len(config.targets) == 1
        assert config.targets[0].name == 'test-db'


class TestFieldClassificationValidation:
    """Test FieldClassification validation logic."""
    
    def test_field_classification_confidence_range(self):
        """Test that confidence values are within valid range."""
        classification = FieldClassification(
            field_name='email',
            is_sensitive=True,
            sensitivity_type='email',
            confidence=0.95,
            reasoning='Pattern match',
            recommended_strategy='bedrock_generation'
        )
        
        assert 0.0 <= classification.confidence <= 1.0
    
    def test_field_classification_with_pattern_matches(self):
        """Test FieldClassification with pattern matches."""
        classification = FieldClassification(
            field_name='email',
            is_sensitive=True,
            sensitivity_type='email',
            confidence=0.95,
            reasoning='Pattern match',
            recommended_strategy='bedrock_generation',
            pattern_matches=['email_regex', 'domain_check']
        )
        
        assert len(classification.pattern_matches) == 2
        assert 'email_regex' in classification.pattern_matches


class TestSensitivityReportValidation:
    """Test SensitivityReport validation and helper methods."""
    
    def test_get_sensitive_fields(self):
        """Test getting list of sensitive fields."""
        classifications = {
            'email': FieldClassification(
                field_name='email',
                is_sensitive=True,
                sensitivity_type='email',
                confidence=0.95,
                reasoning='Pattern match',
                recommended_strategy='bedrock_generation'
            ),
            'age': FieldClassification(
                field_name='age',
                is_sensitive=False,
                sensitivity_type='numeric',
                confidence=0.1,
                reasoning='Not sensitive',
                recommended_strategy='sdv_generation'
            )
        }
        
        report = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=datetime.now(),
            total_fields=2,
            sensitive_fields=1,
            confidence_distribution={'high': 1, 'low': 1}
        )
        
        sensitive = report.get_sensitive_fields()
        assert len(sensitive) == 1
        assert 'email' in sensitive
    
    def test_get_non_sensitive_fields(self):
        """Test getting list of non-sensitive fields."""
        classifications = {
            'email': FieldClassification(
                field_name='email',
                is_sensitive=True,
                sensitivity_type='email',
                confidence=0.95,
                reasoning='Pattern match',
                recommended_strategy='bedrock_generation'
            ),
            'age': FieldClassification(
                field_name='age',
                is_sensitive=False,
                sensitivity_type='numeric',
                confidence=0.1,
                reasoning='Not sensitive',
                recommended_strategy='sdv_generation'
            )
        }
        
        report = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=datetime.now(),
            total_fields=2,
            sensitive_fields=1,
            confidence_distribution={'high': 1, 'low': 1}
        )
        
        non_sensitive = report.get_non_sensitive_fields()
        assert len(non_sensitive) == 1
        assert 'age' in non_sensitive


class TestQualityMetricsValidation:
    """Test QualityMetrics validation logic."""
    
    def test_quality_metrics_score_ranges(self):
        """Test that quality scores are within valid ranges."""
        metrics = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92
        )
        
        assert 0.0 <= metrics.sdv_quality_score <= 1.0
        assert 0.0 <= metrics.column_shapes_score <= 1.0
        assert 0.0 <= metrics.column_pair_trends_score <= 1.0
        assert 0.0 <= metrics.correlation_preservation <= 1.0
        assert 0.0 <= metrics.edge_case_frequency_match <= 1.0
    
    def test_quality_metrics_with_field_scores(self):
        """Test QualityMetrics with per-field scores."""
        metrics = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92,
            field_scores={'email': 0.88, 'age': 0.92}
        )
        
        assert len(metrics.field_scores) == 2
        assert metrics.field_scores['email'] == 0.88


class TestSyntheticDatasetValidation:
    """Test SyntheticDataset validation logic."""
    
    def test_synthetic_dataset_num_records_auto_calculated(self):
        """Test that num_records is auto-calculated from DataFrame."""
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        metrics = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92
        )
        
        dataset = SyntheticDataset(
            data=df,
            quality_metrics=metrics,
            generation_metadata={},
            timestamp=datetime.now()
        )
        
        assert dataset.num_records == 3
    
    def test_synthetic_dataset_with_seed(self):
        """Test SyntheticDataset with random seed."""
        df = pd.DataFrame({'col1': [1, 2]})
        metrics = QualityMetrics(
            sdv_quality_score=0.85,
            column_shapes_score=0.90,
            column_pair_trends_score=0.80,
            ks_tests={},
            correlation_preservation=0.95,
            edge_case_frequency_match=0.92
        )
        
        dataset = SyntheticDataset(
            data=df,
            quality_metrics=metrics,
            generation_metadata={},
            timestamp=datetime.now(),
            seed=42
        )
        
        assert dataset.seed == 42


class TestTestResultsValidation:
    """Test TestResults validation and calculations."""
    
    def test_test_results_pass_rate_calculation(self):
        """Test pass rate calculation."""
        results = TestResults(
            total=10,
            passed=7,
            failed=3
        )
        
        assert results.pass_rate == 70.0
    
    def test_test_results_pass_rate_zero_total(self):
        """Test pass rate with zero total tests."""
        results = TestResults(
            total=0,
            passed=0,
            failed=0
        )
        
        assert results.pass_rate == 0.0
    
    def test_test_results_total_duration_auto_calculated(self):
        """Test that total_duration is auto-calculated from results."""
        result1 = TestResult(
            test_id='test-1',
            test_name='Test 1',
            status='passed',
            duration=1.5,
            logs='Passed'
        )
        result2 = TestResult(
            test_id='test-2',
            test_name='Test 2',
            status='passed',
            duration=2.5,
            logs='Passed'
        )
        
        results = TestResults(
            total=2,
            passed=2,
            failed=0,
            results=[result1, result2]
        )
        
        assert results.total_duration == 4.0


class TestWorkflowExecutionValidation:
    """Test WorkflowExecution validation logic."""
    
    def test_workflow_execution_status_enum(self):
        """Test that status is properly handled as enum."""
        execution = WorkflowExecution(
            id='exec-id',
            config_id='config-id',
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now()
        )
        
        assert execution.status == WorkflowStatus.RUNNING
        assert execution.status.value == 'running'
    
    def test_workflow_execution_default_costs(self):
        """Test default cost values."""
        execution = WorkflowExecution(
            id='exec-id',
            config_id='config-id',
            status=WorkflowStatus.PENDING,
            started_at=datetime.now()
        )
        
        assert execution.total_cost_usd == 0.0
        assert execution.cost_breakdown == {}



# ============================================================================
# Database CRUD Operation Tests
# ============================================================================

class TestDatabaseCRUDOperations:
    """Test database CRUD operations using ORM mapper."""
    
    def test_workflow_config_to_orm_conversion(self):
        """Test converting WorkflowConfig dataclass to ORM model."""
        from shared.utils.orm_mapper import ORMMapper
        
        config = WorkflowConfig(
            id='550e8400-e29b-41d4-a716-446655440000',
            name='Test Config',
            description='Test description',
            created_by='test_user',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            production_data_path=Path('/data/test.csv'),
            tags=['test', 'demo']
        )
        
        orm_config = ORMMapper.workflow_config_to_orm(config)
        
        assert orm_config.name == 'Test Config'
        assert orm_config.description == 'Test description'
        assert orm_config.created_by == 'test_user'
        assert orm_config.tags == ['test', 'demo']
        assert 'production_data_path' in orm_config.config_json
    
    def test_workflow_config_from_orm_conversion(self):
        """Test converting ORM model back to WorkflowConfig dataclass."""
        from shared.utils.orm_mapper import ORMMapper
        from shared.database.schema import WorkflowConfig as WorkflowConfigORM
        import uuid
        
        config_dict = {
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'name': 'Test Config',
            'description': 'Test description',
            'created_by': 'test_user',
            'created_at': '2024-01-01T12:00:00',
            'production_data_path': '/data/test.csv',
            'sdv_model': 'gaussian_copula',
            'num_synthetic_records': 1000,
            'targets': []
        }
        
        orm_config = WorkflowConfigORM(
            id=uuid.UUID('550e8400-e29b-41d4-a716-446655440000'),
            name='Test Config',
            description='Test description',
            config_json=config_dict,
            created_by='test_user',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            tags=['test']
        )
        
        config = ORMMapper.workflow_config_from_orm(orm_config)
        
        assert config.name == 'Test Config'
        assert config.description == 'Test description'
        assert isinstance(config.production_data_path, Path)
    
    def test_workflow_execution_to_orm_conversion(self):
        """Test converting WorkflowExecution dataclass to ORM model."""
        from shared.utils.orm_mapper import ORMMapper
        
        execution = WorkflowExecution(
            id='550e8400-e29b-41d4-a716-446655440001',
            config_id='550e8400-e29b-41d4-a716-446655440000',
            status=WorkflowStatus.RUNNING,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            current_agent='data_processor',
            total_cost_usd=1.25
        )
        
        orm_execution = ORMMapper.workflow_execution_to_orm(execution)
        
        assert orm_execution.status == 'running'
        assert orm_execution.checkpoint_data['current_agent'] == 'data_processor'
        assert orm_execution.checkpoint_data['total_cost_usd'] == 1.25
    
    def test_workflow_execution_from_orm_conversion(self):
        """Test converting ORM model back to WorkflowExecution dataclass."""
        from shared.utils.orm_mapper import ORMMapper
        from shared.database.schema import WorkflowExecution as WorkflowExecutionORM
        import uuid
        
        checkpoint_data = {
            'current_agent': 'data_processor',
            'agent_progress': {'step': 1},
            'total_cost_usd': 1.25,
            'cost_breakdown': {'bedrock': 1.0, 's3': 0.25}
        }
        
        orm_execution = WorkflowExecutionORM(
            id=uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            config_id=uuid.UUID('550e8400-e29b-41d4-a716-446655440000'),
            status='running',
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            checkpoint_data=checkpoint_data
        )
        
        execution = ORMMapper.workflow_execution_from_orm(orm_execution)
        
        assert execution.status == WorkflowStatus.RUNNING
        assert execution.current_agent == 'data_processor'
        assert execution.total_cost_usd == 1.25
        assert execution.cost_breakdown == {'bedrock': 1.0, 's3': 0.25}
    
    def test_orm_round_trip_preserves_data(self):
        """Test that ORM round trip preserves all data."""
        from shared.utils.orm_mapper import ORMMapper
        from shared.database.schema import WorkflowConfig as WorkflowConfigORM
        
        original = WorkflowConfig(
            id='550e8400-e29b-41d4-a716-446655440000',
            name='Test Config',
            description='Test description',
            created_by='test_user',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            production_data_path=Path('/data/test.csv'),
            sdv_model='ctgan',
            num_synthetic_records=5000,
            tags=['test', 'demo']
        )
        
        # Convert to ORM
        orm_config = ORMMapper.workflow_config_to_orm(original)
        
        # Convert back to dataclass
        restored = ORMMapper.workflow_config_from_orm(orm_config)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.sdv_model == original.sdv_model
        assert restored.num_synthetic_records == original.num_synthetic_records
        assert restored.tags == original.tags


# ============================================================================
# File Loading Utility Tests
# ============================================================================

class TestDataLoaderCSV:
    """Test CSV file loading functionality."""
    
    def test_load_csv_file_not_found(self):
        """Test loading non-existent CSV file raises FileNotFoundError."""
        from shared.utils.data_loader import DataLoader
        
        with pytest.raises(FileNotFoundError):
            DataLoader.load_csv('/nonexistent/file.csv')
    
    def test_load_csv_with_sample_data(self, tmp_path):
        """Test loading valid CSV file."""
        from shared.utils.data_loader import DataLoader
        
        # Create sample CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2,col3\n1,a,10.5\n2,b,20.5\n3,c,30.5")
        
        df = DataLoader.load_csv(csv_file)
        
        assert len(df) == 3
        assert list(df.columns) == ['col1', 'col2', 'col3']
        assert df['col1'].tolist() == [1, 2, 3]
    
    def test_load_csv_with_missing_values(self, tmp_path):
        """Test loading CSV with missing values."""
        from shared.utils.data_loader import DataLoader
        
        csv_file = tmp_path / "test_na.csv"
        csv_file.write_text("col1,col2,col3\n1,a,10.5\n2,,20.5\n3,c,NA")
        
        df = DataLoader.load_csv(csv_file)
        
        assert df['col2'].isna().sum() == 1
        assert df['col3'].isna().sum() == 1
    
    def test_load_csv_with_custom_encoding(self, tmp_path):
        """Test loading CSV with custom encoding."""
        from shared.utils.data_loader import DataLoader
        
        csv_file = tmp_path / "test_utf8.csv"
        csv_file.write_text("name,value\nTest,123", encoding='utf-8')
        
        df = DataLoader.load_csv(csv_file, encoding='utf-8')
        
        assert len(df) == 1
        assert df['name'].iloc[0] == 'Test'


class TestDataLoaderJSON:
    """Test JSON file loading functionality."""
    
    def test_load_json_file_not_found(self):
        """Test loading non-existent JSON file raises FileNotFoundError."""
        from shared.utils.data_loader import DataLoader
        
        with pytest.raises(FileNotFoundError):
            DataLoader.load_json('/nonexistent/file.json')
    
    def test_load_json_records_format(self, tmp_path):
        """Test loading JSON file in records format."""
        from shared.utils.data_loader import DataLoader
        import json
        
        json_file = tmp_path / "test.json"
        data = [
            {'col1': 1, 'col2': 'a', 'col3': 10.5},
            {'col1': 2, 'col2': 'b', 'col3': 20.5},
            {'col1': 3, 'col2': 'c', 'col3': 30.5}
        ]
        json_file.write_text(json.dumps(data))
        
        df = DataLoader.load_json(json_file, orient='records')
        
        assert len(df) == 3
        assert list(df.columns) == ['col1', 'col2', 'col3']
    
    def test_load_json_invalid_format(self, tmp_path):
        """Test loading invalid JSON file raises ValueError."""
        from shared.utils.data_loader import DataLoader
        
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json{")
        
        with pytest.raises(ValueError):
            DataLoader.load_json(json_file)


class TestDataLoaderAutoDetect:
    """Test automatic format detection."""
    
    def test_load_data_auto_detect_csv(self, tmp_path):
        """Test auto-detecting CSV format."""
        from shared.utils.data_loader import DataLoader
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\n1,a\n2,b")
        
        df = DataLoader.load_data(csv_file)
        
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2']
    
    def test_load_data_auto_detect_json(self, tmp_path):
        """Test auto-detecting JSON format."""
        from shared.utils.data_loader import DataLoader
        import json
        
        json_file = tmp_path / "test.json"
        data = [{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}]
        json_file.write_text(json.dumps(data))
        
        df = DataLoader.load_data(json_file)
        
        assert len(df) == 2
    
    def test_load_data_unsupported_format(self, tmp_path):
        """Test loading unsupported format raises ValueError."""
        from shared.utils.data_loader import DataLoader
        
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("some text")
        
        with pytest.raises(ValueError, match="Cannot determine file format"):
            DataLoader.load_data(txt_file)
    
    def test_load_data_explicit_format(self, tmp_path):
        """Test loading with explicit format specification."""
        from shared.utils.data_loader import DataLoader
        
        # Create CSV file with .txt extension
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("col1,col2\n1,a\n2,b")
        
        df = DataLoader.load_data(txt_file, file_format='csv')
        
        assert len(df) == 2


class TestDataLoaderSave:
    """Test data saving functionality."""
    
    def test_save_csv(self, tmp_path):
        """Test saving DataFrame to CSV."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        csv_file = tmp_path / "output.csv"
        
        DataLoader.save_csv(df, csv_file)
        
        assert csv_file.exists()
        
        # Load and verify
        loaded_df = DataLoader.load_csv(csv_file)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['col1', 'col2']
    
    def test_save_json(self, tmp_path):
        """Test saving DataFrame to JSON."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        json_file = tmp_path / "output.json"
        
        DataLoader.save_json(df, json_file)
        
        assert json_file.exists()
        
        # Load and verify
        loaded_df = DataLoader.load_json(json_file)
        assert len(loaded_df) == 3
    
    def test_save_creates_parent_directories(self, tmp_path):
        """Test that save operations create parent directories."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({'col1': [1, 2]})
        nested_file = tmp_path / "subdir" / "nested" / "output.csv"
        
        DataLoader.save_csv(df, nested_file)
        
        assert nested_file.exists()


class TestDataLoaderProfile:
    """Test data profiling functionality."""
    
    def test_get_data_profile_numeric_columns(self):
        """Test profiling DataFrame with numeric columns."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000]
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert 'age' in profile
        assert 'salary' in profile
        assert profile['age']['count'] == 5
        assert profile['age']['null_count'] == 0
        assert 'mean' in profile['age']
        assert 'std' in profile['age']
        assert profile['age']['mean'] == 35.0
    
    def test_get_data_profile_string_columns(self):
        """Test profiling DataFrame with string columns."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com']
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert 'name' in profile
        assert 'email' in profile
        assert 'avg_length' in profile['name']
        assert 'min_length' in profile['name']
        assert 'max_length' in profile['name']
    
    def test_get_data_profile_with_nulls(self):
        """Test profiling DataFrame with null values."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['a', None, 'c', None, 'e']
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert profile['col1']['null_count'] == 1
        assert profile['col1']['null_percentage'] == 20.0
        assert profile['col2']['null_count'] == 2
        assert profile['col2']['null_percentage'] == 40.0
    
    def test_get_data_profile_unique_counts(self):
        """Test profiling includes unique value counts."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({
            'category': ['A', 'B', 'A', 'C', 'B', 'A'],
            'value': [1, 2, 1, 3, 2, 1]
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert profile['category']['unique_count'] == 3
        assert profile['value']['unique_count'] == 3
    
    def test_get_data_profile_sample_values(self):
        """Test profiling includes sample values."""
        from shared.utils.data_loader import DataLoader
        
        df = pd.DataFrame({
            'col1': list(range(20))
        })
        
        profile = DataLoader.get_data_profile(df)
        
        assert 'sample_values' in profile['col1']
        assert len(profile['col1']['sample_values']) == 10  # First 10 values
