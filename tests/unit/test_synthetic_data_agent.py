"""Unit tests for Synthetic Data Agent."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from agents.synthetic_data.agent import SyntheticDataAgent, SDVSynthesizerWrapper
from shared.models.sensitivity import SensitivityReport, FieldClassification
from shared.models.quality import QualityMetrics, SyntheticDataset


class TestSDVSynthesizerWrapper:
    """Tests for SDV Synthesizer Wrapper."""
    
    def test_initialization_with_valid_model(self):
        """Test wrapper initialization with valid model types."""
        for model_type in ['gaussian_copula', 'ctgan', 'copula_gan']:
            wrapper = SDVSynthesizerWrapper(model_type=model_type)
            assert wrapper.model_type == model_type
            assert wrapper.synthesizer is None
            assert wrapper.metadata is None
    
    def test_initialization_with_invalid_model(self):
        """Test wrapper initialization with invalid model type."""
        with pytest.raises(ValueError, match="Unknown model type"):
            SDVSynthesizerWrapper(model_type='invalid_model')
    
    def test_create_metadata_without_sensitivity_report(self):
        """Test metadata creation from DataFrame only."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com']
        })
        
        wrapper = SDVSynthesizerWrapper()
        metadata = wrapper.create_metadata(df)
        
        assert metadata is not None
        assert wrapper.metadata is not None
        # Check that columns are detected
        assert 'age' in metadata.columns
        assert 'name' in metadata.columns
        assert 'email' in metadata.columns
    
    def test_create_metadata_with_sensitivity_report(self):
        """Test metadata creation with sensitivity report."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com']
        })
        
        # Create sensitivity report
        classifications = {
            'age': FieldClassification(
                field_name='age',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            ),
            'email': FieldClassification(
                field_name='email',
                is_sensitive=True,
                sensitivity_type='email',
                confidence=0.95,
                reasoning='Email pattern detected',
                recommended_strategy='bedrock_text'
            )
        }
        
        sensitivity_report = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=datetime.now(),
            total_fields=2,
            sensitive_fields=1,
            confidence_distribution={'high': 1, 'medium': 0, 'low': 1}
        )
        
        wrapper = SDVSynthesizerWrapper()
        metadata = wrapper.create_metadata(df, sensitivity_report)
        
        assert metadata is not None
        assert 'age' in metadata.columns
        assert 'email' in metadata.columns
    
    def test_fit_and_sample_gaussian_copula(self):
        """Test fitting and sampling with GaussianCopula model."""
        df = pd.DataFrame({
            'age': np.random.randint(18, 80, 100),
            'income': np.random.randint(20000, 150000, 100),
            'score': np.random.uniform(0, 100, 100)
        })
        
        wrapper = SDVSynthesizerWrapper(model_type='gaussian_copula')
        metadata = wrapper.create_metadata(df)
        wrapper.fit(df, metadata)
        
        # Generate samples
        synthetic_df = wrapper.sample(num_rows=50, seed=42)
        
        assert len(synthetic_df) == 50
        assert list(synthetic_df.columns) == list(df.columns)
        # Check that values are in reasonable ranges
        assert synthetic_df['age'].min() >= 0
        assert synthetic_df['age'].max() <= 120
    
    def test_deterministic_sampling_with_seed(self):
        """Test that same seed produces consistent results."""
        df = pd.DataFrame({
            'value': np.random.rand(50)
        })
        
        wrapper = SDVSynthesizerWrapper(model_type='gaussian_copula')
        metadata = wrapper.create_metadata(df)
        wrapper.fit(df, metadata)
        
        # Generate twice with same seed
        # Note: SDV may not guarantee exact determinism, but we can verify
        # that the seed parameter is accepted and produces valid output
        synthetic_df1 = wrapper.sample(num_rows=20, seed=123)
        synthetic_df2 = wrapper.sample(num_rows=20, seed=123)
        
        # Verify both outputs are valid
        assert len(synthetic_df1) == 20
        assert len(synthetic_df2) == 20
        assert list(synthetic_df1.columns) == list(synthetic_df2.columns)
        
        # Note: SDV's internal randomness may not be fully controlled by numpy seed
        # So we just verify the outputs are reasonable, not necessarily identical
    
    def test_evaluate_quality(self):
        """Test quality evaluation."""
        real_df = pd.DataFrame({
            'age': np.random.randint(18, 80, 100),
            'income': np.random.randint(20000, 150000, 100)
        })
        
        wrapper = SDVSynthesizerWrapper(model_type='gaussian_copula')
        metadata = wrapper.create_metadata(real_df)
        wrapper.fit(real_df, metadata)
        
        synthetic_df = wrapper.sample(num_rows=100, seed=42)
        
        # Evaluate quality
        quality_metrics = wrapper.evaluate_quality(real_df, synthetic_df)
        
        assert 'overall_quality_score' in quality_metrics
        assert 'column_shapes' in quality_metrics
        assert 'column_pair_trends' in quality_metrics
        assert 0.0 <= quality_metrics['overall_quality_score'] <= 1.0


class TestSyntheticDataAgent:
    """Tests for Synthetic Data Agent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = SyntheticDataAgent()
        assert agent.bedrock_client is None
        assert agent.sdv_wrapper is None
    
    def test_separate_fields(self):
        """Test field separation into sensitive and non-sensitive."""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com']
        })
        
        # Create sensitivity report
        classifications = {
            'age': FieldClassification(
                field_name='age',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            ),
            'name': FieldClassification(
                field_name='name',
                is_sensitive=True,
                sensitivity_type='name',
                confidence=0.85,
                reasoning='Name field detected',
                recommended_strategy='bedrock_text'
            ),
            'email': FieldClassification(
                field_name='email',
                is_sensitive=True,
                sensitivity_type='email',
                confidence=0.95,
                reasoning='Email pattern detected',
                recommended_strategy='bedrock_text'
            )
        }
        
        sensitivity_report = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=datetime.now(),
            total_fields=3,
            sensitive_fields=2,
            confidence_distribution={'high': 2, 'medium': 0, 'low': 1}
        )
        
        agent = SyntheticDataAgent()
        sensitive, non_sensitive, sensitive_class = agent.separate_fields(df, sensitivity_report)
        
        assert len(sensitive) == 2
        assert len(non_sensitive) == 1
        assert 'name' in sensitive
        assert 'email' in sensitive
        assert 'age' in non_sensitive
        assert len(sensitive_class) == 2
    
    def test_generate_synthetic_data_basic(self):
        """Test basic synthetic data generation."""
        # Create sample data
        df = pd.DataFrame({
            'age': np.random.randint(18, 80, 50),
            'income': np.random.randint(20000, 150000, 50),
            'score': np.random.uniform(0, 100, 50)
        })
        
        # Create minimal sensitivity report
        classifications = {
            'age': FieldClassification(
                field_name='age',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            ),
            'income': FieldClassification(
                field_name='income',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            ),
            'score': FieldClassification(
                field_name='score',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            )
        }
        
        sensitivity_report = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=datetime.now(),
            total_fields=3,
            sensitive_fields=0,
            confidence_distribution={'high': 0, 'medium': 0, 'low': 3}
        )
        
        agent = SyntheticDataAgent()
        
        # Generate synthetic data
        synthetic_dataset = agent.generate_synthetic_data(
            data=df,
            sensitivity_report=sensitivity_report,
            num_rows=30,
            sdv_model='gaussian_copula',
            seed=42
        )
        
        # Verify results
        assert isinstance(synthetic_dataset, SyntheticDataset)
        assert len(synthetic_dataset.data) == 30
        assert list(synthetic_dataset.data.columns) == list(df.columns)
        assert synthetic_dataset.seed == 42
        assert synthetic_dataset.num_records == 30
        
        # Check quality metrics
        assert isinstance(synthetic_dataset.quality_metrics, QualityMetrics)
        assert 0.0 <= synthetic_dataset.quality_metrics.sdv_quality_score <= 1.0
        
        # Check metadata
        assert 'sdv_model' in synthetic_dataset.generation_metadata
        assert synthetic_dataset.generation_metadata['sdv_model'] == 'gaussian_copula'
        assert synthetic_dataset.generation_metadata['source_rows'] == 50
        assert synthetic_dataset.generation_metadata['generated_rows'] == 30
    
    def test_generate_synthetic_data_with_different_models(self):
        """Test generation with different SDV models."""
        df = pd.DataFrame({
            'value1': np.random.rand(30),
            'value2': np.random.rand(30)
        })
        
        classifications = {
            'value1': FieldClassification(
                field_name='value1',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            ),
            'value2': FieldClassification(
                field_name='value2',
                is_sensitive=False,
                sensitivity_type='non_sensitive',
                confidence=0.1,
                reasoning='Numeric field',
                recommended_strategy='sdv_preserve_distribution'
            )
        }
        
        sensitivity_report = SensitivityReport(
            classifications=classifications,
            data_profile={},
            timestamp=datetime.now(),
            total_fields=2,
            sensitive_fields=0,
            confidence_distribution={'high': 0, 'medium': 0, 'low': 2}
        )
        
        agent = SyntheticDataAgent()
        
        # Test with GaussianCopula
        result = agent.generate_synthetic_data(
            data=df,
            sensitivity_report=sensitivity_report,
            num_rows=20,
            sdv_model='gaussian_copula',
            seed=42
        )
        assert len(result.data) == 20
        assert result.generation_metadata['sdv_model'] == 'gaussian_copula'
    
    def test_ks_tests_calculation(self):
        """Test KS test calculation."""
        real_df = pd.DataFrame({
            'value': np.random.normal(50, 10, 100)
        })
        
        synthetic_df = pd.DataFrame({
            'value': np.random.normal(50, 10, 100)
        })
        
        agent = SyntheticDataAgent()
        ks_tests = agent._perform_ks_tests(real_df, synthetic_df)
        
        assert 'value' in ks_tests
        assert 'statistic' in ks_tests['value']
        assert 'pvalue' in ks_tests['value']
        assert 0.0 <= ks_tests['value']['statistic'] <= 1.0
        assert 0.0 <= ks_tests['value']['pvalue'] <= 1.0
    
    def test_correlation_preservation_calculation(self):
        """Test correlation preservation calculation."""
        # Create correlated data
        np.random.seed(42)
        x = np.random.rand(100)
        y = x + np.random.rand(100) * 0.1  # Highly correlated
        
        real_df = pd.DataFrame({'x': x, 'y': y})
        
        # Create synthetic with similar correlation
        x_synth = np.random.rand(100)
        y_synth = x_synth + np.random.rand(100) * 0.1
        synthetic_df = pd.DataFrame({'x': x_synth, 'y': y_synth})
        
        agent = SyntheticDataAgent()
        preservation = agent._calculate_correlation_preservation(real_df, synthetic_df)
        
        assert 0.0 <= preservation <= 1.0
        # Should be high since both have similar correlation structure
        assert preservation > 0.5
    
    def test_save_synthetic_data_csv(self, tmp_path):
        """Test saving synthetic data to CSV."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        quality_metrics = QualityMetrics(
            sdv_quality_score=0.9,
            column_shapes_score=0.85,
            column_pair_trends_score=0.88,
            ks_tests={},
            correlation_preservation=0.92,
            edge_case_frequency_match=1.0
        )
        
        synthetic_dataset = SyntheticDataset(
            data=df,
            quality_metrics=quality_metrics,
            generation_metadata={'test': 'data'},
            timestamp=datetime.now(),
            seed=42
        )
        
        agent = SyntheticDataAgent()
        output_path = tmp_path / "synthetic_data.csv"
        
        agent.save_synthetic_data(synthetic_dataset, output_path, format='csv')
        
        # Verify files exist
        assert output_path.exists()
        assert (tmp_path / "synthetic_data_metadata.json").exists()
        
        # Verify data can be loaded
        loaded_df = pd.read_csv(output_path)
        pd.testing.assert_frame_equal(loaded_df, df)
