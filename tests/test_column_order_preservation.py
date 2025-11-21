"""End-to-end integration tests for column order preservation."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from datetime import datetime

from agents.data_processor.agent import DataProcessorAgent
from agents.synthetic_data.agent import SyntheticDataAgent
from shared.models.sensitivity import SensitivityReport


class TestColumnOrderPreservation:
    """Test suite for column order preservation through the entire pipeline."""
    
    def test_end_to_end_column_order_preservation(self):
        """Test column order preservation from production data through synthetic generation."""
        # Create production data with specific column order
        production_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 
                     'david@example.com', 'eve@example.com'],
            'age': [30, 25, 35, 28, 32],
            'city': ['NYC', 'LA', 'Chicago', 'Boston', 'Seattle']
        })
        
        original_order = list(production_data.columns)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            production_data.to_csv(f.name, index=False)
            data_file = Path(f.name)
        
        try:
            # Process through Data Processor Agent
            data_processor = DataProcessorAgent()
            sensitivity_report = data_processor.process(data_file)
            
            # Verify column order captured
            assert sensitivity_report.column_order == original_order, \
                f"Column order not captured correctly. Expected: {original_order}, Got: {sensitivity_report.column_order}"
            
            # Generate synthetic data
            synthetic_agent = SyntheticDataAgent()
            synthetic_dataset = synthetic_agent.generate_synthetic_data(
                data=production_data,
                sensitivity_report=sensitivity_report,
                num_rows=10,
                sdv_model='gaussian_copula',
                seed=42
            )
            
            # Verify column order preserved in synthetic data
            synthetic_order = list(synthetic_dataset.data.columns)
            assert synthetic_order == original_order, \
                f"Column order not preserved. Expected: {original_order}, Got: {synthetic_order}"
            
            # Verify quality metrics report column order preservation
            assert synthetic_dataset.quality_metrics.column_order_preserved, \
                "Quality metrics should report column order as preserved"
            
            # Verify column order report
            column_order_report = synthetic_dataset.quality_metrics.column_order_report
            assert column_order_report['order_preserved'], \
                "Column order report should indicate order is preserved"
            assert column_order_report['original_order'] == original_order
            assert column_order_report['synthetic_order'] == original_order
            
            # Export to CSV and verify
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
                synthetic_dataset.data.to_csv(f.name, index=False)
                csv_path = Path(f.name)
            
            try:
                df_read = pd.read_csv(csv_path)
                csv_order = list(df_read.columns)
                assert csv_order == original_order, \
                    f"Column order not preserved in CSV export. Expected: {original_order}, Got: {csv_order}"
            finally:
                csv_path.unlink()
                
        finally:
            data_file.unlink()
    
    def test_column_order_with_different_orderings(self):
        """Test column order preservation with various column orderings."""
        test_cases = [
            ['a', 'b', 'c', 'd', 'e'],
            ['z', 'y', 'x', 'w', 'v'],
            ['col_1', 'col_2', 'col_3'],
            ['field_z', 'field_a', 'field_m'],
        ]
        
        for column_order in test_cases:
            # Create DataFrame with specific column order
            data = {col: list(range(5)) for col in column_order}
            df = pd.DataFrame(data)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
                df.to_csv(f.name, index=False)
                data_file = Path(f.name)
            
            try:
                # Process through Data Processor Agent
                data_processor = DataProcessorAgent()
                sensitivity_report = data_processor.process(data_file)
                
                # Verify column order captured
                assert sensitivity_report.column_order == column_order, \
                    f"Column order not captured for {column_order}"
                
                # Generate synthetic data
                synthetic_agent = SyntheticDataAgent()
                synthetic_dataset = synthetic_agent.generate_synthetic_data(
                    data=df,
                    sensitivity_report=sensitivity_report,
                    num_rows=5,
                    sdv_model='gaussian_copula',
                    seed=42
                )
                
                # Verify column order preserved
                synthetic_order = list(synthetic_dataset.data.columns)
                assert synthetic_order == column_order, \
                    f"Column order not preserved for {column_order}. Got: {synthetic_order}"
                    
            finally:
                data_file.unlink()
    
    def test_column_order_validation_detects_mismatch(self):
        """Test that column order validation correctly detects mismatches."""
        from shared.utils.validation import validate_column_order
        
        original = ['a', 'b', 'c', 'd']
        synthetic = ['a', 'c', 'b', 'd']
        
        report = validate_column_order(original, synthetic)
        
        assert not report['order_preserved'], "Should detect column order mismatch"
        assert 'mismatches' in report, "Should include mismatch details"
        assert len(report['mismatches']) > 0, "Should report at least one mismatch"
        
        # Check specific mismatch
        mismatches = report['mismatches']
        assert any(m['position'] == 1 and m['expected'] == 'b' and m['actual'] == 'c' 
                  for m in mismatches), "Should detect position 1 mismatch"
    
    def test_column_order_validation_with_missing_columns(self):
        """Test column order validation with missing columns."""
        from shared.utils.validation import validate_column_order
        
        original = ['a', 'b', 'c', 'd']
        synthetic = ['a', 'b', 'd']  # Missing 'c'
        
        report = validate_column_order(original, synthetic)
        
        assert not report['order_preserved'], "Should detect missing column"
        assert 'missing_columns' in report, "Should include missing columns"
        assert 'c' in report['missing_columns'], "Should report 'c' as missing"
    
    def test_column_order_validation_with_extra_columns(self):
        """Test column order validation with extra columns."""
        from shared.utils.validation import validate_column_order
        
        original = ['a', 'b', 'c']
        synthetic = ['a', 'b', 'c', 'd']  # Extra 'd'
        
        report = validate_column_order(original, synthetic)
        
        assert not report['order_preserved'], "Should detect extra column"
        assert 'extra_columns' in report, "Should include extra columns"
        assert 'd' in report['extra_columns'], "Should report 'd' as extra"
    
    def test_enforce_column_order_method(self):
        """Test the _enforce_column_order method directly."""
        # Create DataFrame with wrong column order
        df = pd.DataFrame({
            'c': [1, 2, 3],
            'a': [4, 5, 6],
            'b': [7, 8, 9]
        })
        
        target_order = ['a', 'b', 'c']
        
        agent = SyntheticDataAgent()
        reordered = agent._enforce_column_order(df, target_order)
        
        assert list(reordered.columns) == target_order, \
            f"Columns not reordered correctly. Expected: {target_order}, Got: {list(reordered.columns)}"
        
        # Verify data integrity
        assert reordered['a'].tolist() == [4, 5, 6]
        assert reordered['b'].tolist() == [7, 8, 9]
        assert reordered['c'].tolist() == [1, 2, 3]
    
    def test_generation_metadata_includes_column_order(self):
        """Test that generation metadata includes column order information."""
        production_data = pd.DataFrame({
            'field1': [1, 2, 3],
            'field2': [4, 5, 6],
            'field3': [7, 8, 9]
        })
        
        original_order = list(production_data.columns)
        
        # Create mock sensitivity report
        sensitivity_report = SensitivityReport(
            classifications={},
            data_profile={},
            column_order=original_order,
            timestamp=datetime.now(),
            total_fields=len(production_data.columns),
            sensitive_fields=0,
            confidence_distribution={'high': 0, 'medium': 0, 'low': 0}
        )
        
        # Generate synthetic data
        synthetic_agent = SyntheticDataAgent()
        synthetic_dataset = synthetic_agent.generate_synthetic_data(
            data=production_data,
            sensitivity_report=sensitivity_report,
            num_rows=5,
            sdv_model='gaussian_copula',
            seed=42
        )
        
        # Verify generation metadata includes column order info
        metadata = synthetic_dataset.generation_metadata
        assert 'original_column_order' in metadata, "Metadata should include original column order"
        assert 'final_column_order' in metadata, "Metadata should include final column order"
        assert 'column_order_preserved' in metadata, "Metadata should include column order preserved flag"
        
        assert metadata['original_column_order'] == original_order
        assert metadata['final_column_order'] == original_order
        assert metadata['column_order_preserved'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
