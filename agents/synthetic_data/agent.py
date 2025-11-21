"""Synthetic Data Agent for generating GDPR-compliant synthetic datasets."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

# SDV imports
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer, CopulaGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdv.evaluation.single_table import evaluate_quality, run_diagnostic

from shared.models.sensitivity import SensitivityReport, FieldClassification
from shared.models.quality import QualityMetrics, SyntheticDataset
from shared.utils.bedrock_client import BedrockClient, BedrockConfig, RuleBasedTextGenerator
from shared.utils.edge_case_generator import (
    EdgeCaseGenerator, EdgeCaseRule, EdgeCaseType, EdgeCasePatternLibrary
)
from shared.utils.validation import validate_column_order
from shared.utils.agent_logger import AgentLogger

# Configure logging
logger = logging.getLogger(__name__)


class SDVSynthesizerWrapper:
    """Wrapper for SDV synthesizers with unified interface."""
    
    # Map of model names to SDV synthesizer classes
    SYNTHESIZER_CLASSES = {
        'gaussian_copula': GaussianCopulaSynthesizer,
        'ctgan': CTGANSynthesizer,
        'copula_gan': CopulaGANSynthesizer,
    }
    
    def __init__(self, model_type: str = 'gaussian_copula', **model_params):
        """Initialize SDV synthesizer wrapper.
        
        Args:
            model_type: Type of SDV model ('gaussian_copula', 'ctgan', 'copula_gan')
            **model_params: Additional parameters for the synthesizer
        """
        if model_type not in self.SYNTHESIZER_CLASSES:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Must be one of {list(self.SYNTHESIZER_CLASSES.keys())}"
            )
        
        self.model_type = model_type
        
        # Filter model params based on model type
        # GaussianCopula doesn't support epochs/batch_size (not a neural network)
        # CTGAN and CopulaGAN support these parameters
        if model_type == 'gaussian_copula':
            # Remove neural network specific params
            filtered_params = {k: v for k, v in model_params.items() 
                             if k not in ['epochs', 'batch_size']}
            if filtered_params != model_params:
                logger.info(f"Filtered out neural network params for GaussianCopula: {set(model_params.keys()) - set(filtered_params.keys())}")
            self.model_params = filtered_params
        else:
            # CTGAN and CopulaGAN can use all params
            self.model_params = model_params
        
        self.synthesizer = None
        self.metadata = None
        
        logger.info(f"Initialized SDV synthesizer wrapper with model: {model_type}, params: {self.model_params}")
    
    def create_metadata(
        self,
        data: pd.DataFrame,
        sensitivity_report: Optional[SensitivityReport] = None
    ) -> SingleTableMetadata:
        """Create SDV metadata from DataFrame and sensitivity report.
        
        Args:
            data: Source DataFrame
            sensitivity_report: Optional sensitivity report with field classifications
            
        Returns:
            SingleTableMetadata object configured for the data
        """
        # Detect metadata from DataFrame
        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(data)
        
        # If sensitivity report provided, update metadata with constraints
        if sensitivity_report:
            for field_name, classification in sensitivity_report.classifications.items():
                if field_name not in data.columns:
                    continue
                
                # Get column metadata
                column_meta = metadata.columns.get(field_name, {})
                
                # Add semantic type information based on sensitivity classification
                if classification.is_sensitive:
                    # For sensitive fields, we'll handle them separately
                    # Mark them for special handling
                    if 'sdtype' in column_meta:
                        # Keep the detected sdtype but add a note
                        logger.info(
                            f"Field '{field_name}' is sensitive ({classification.sensitivity_type}), "
                            f"will be handled with strategy: {classification.recommended_strategy}"
                        )
        
        self.metadata = metadata
        return metadata
    
    def fit(self, data: pd.DataFrame, metadata: Optional[SingleTableMetadata] = None, seed: Optional[int] = None):
        """Fit the synthesizer to the data.
        
        Args:
            data: Training data
            metadata: Optional metadata (will be created if not provided)
            seed: Random seed for reproducible fitting
        """
        if metadata is None:
            if self.metadata is None:
                raise ValueError("Metadata must be provided or created first")
            metadata = self.metadata
        else:
            self.metadata = metadata
        
        # Set random seeds for reproducible fitting
        if seed is not None:
            self._set_random_seeds(seed)
        
        # Create synthesizer instance
        synthesizer_class = self.SYNTHESIZER_CLASSES[self.model_type]
        self.synthesizer = synthesizer_class(
            metadata=metadata,
            **self.model_params
        )
        
        logger.info(f"Fitting {self.model_type} synthesizer to data with {len(data)} rows, seed={seed}")
        
        # Fit the model
        self.synthesizer.fit(data)
        
        logger.info("Synthesizer fitting complete")
    
    def sample(self, num_rows: int, seed: Optional[int] = None) -> pd.DataFrame:
        """Generate synthetic samples.
        
        Args:
            num_rows: Number of rows to generate
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with synthetic data
        """
        if self.synthesizer is None:
            raise ValueError("Synthesizer must be fitted before sampling")
        
        logger.info(f"Generating {num_rows} synthetic rows with seed={seed}")
        
        # Set random seeds for reproducibility
        if seed is not None:
            self._set_random_seeds(seed)
        
        # Generate samples
        synthetic_data = self.synthesizer.sample(num_rows=num_rows)
        
        logger.info(f"Generated {len(synthetic_data)} synthetic rows")
        
        return synthetic_data
    
    def _set_random_seeds(self, seed: int):
        """Set all random seeds for reproducibility.
        
        Args:
            seed: Random seed value
        """
        import random
        np.random.seed(seed)
        random.seed(seed)
        
        # Set PyTorch seed if available (needed for CTGAN and CopulaGAN)
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            # PyTorch not available, skip
            pass
    
    def evaluate_quality(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Evaluate quality of synthetic data using SDV metrics.
        
        Args:
            real_data: Original data
            synthetic_data: Generated synthetic data
            
        Returns:
            Dictionary with quality metrics
        """
        if self.metadata is None:
            raise ValueError("Metadata must be created before evaluation")
        
        logger.info("Evaluating synthetic data quality")
        
        # Use SDV's evaluate_quality function
        quality_report = evaluate_quality(
            real_data=real_data,
            synthetic_data=synthetic_data,
            metadata=self.metadata
        )
        
        # Extract metrics
        metrics = {
            'overall_quality_score': quality_report.get_score(),
            'column_shapes': quality_report.get_details(property_name='Column Shapes'),
            'column_pair_trends': quality_report.get_details(property_name='Column Pair Trends'),
        }
        
        logger.info(f"Quality evaluation complete. Overall score: {metrics['overall_quality_score']:.3f}")
        
        return metrics


class SyntheticDataAgent:
    """Agent for generating synthetic data using SDV and Bedrock."""
    
    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        bedrock_config: Optional[BedrockConfig] = None,
        edge_case_generator: Optional[EdgeCaseGenerator] = None,
        agent_logger: Optional[AgentLogger] = None
    ):
        """Initialize Synthetic Data Agent.
        
        Args:
            bedrock_client: Optional BedrockClient for text field generation
            bedrock_config: Optional BedrockConfig for Bedrock parameters
            edge_case_generator: Optional EdgeCaseGenerator for edge case injection
            agent_logger: Optional AgentLogger for structured logging
        """
        self.bedrock_client = bedrock_client
        self.bedrock_config = bedrock_config or BedrockConfig()
        self.sdv_wrapper = None
        self.fallback_generator = RuleBasedTextGenerator()
        self.edge_case_generator = edge_case_generator or EdgeCaseGenerator()
        self.agent_logger = agent_logger
        
        # Pass agent_logger to bedrock_client if available
        if self.bedrock_client and self.agent_logger:
            self.bedrock_client.agent_logger = self.agent_logger
        
        logger.info("Initialized Synthetic Data Agent")
    
    def separate_fields(
        self,
        data: pd.DataFrame,
        sensitivity_report: SensitivityReport
    ) -> tuple[List[str], List[str], Dict[str, FieldClassification]]:
        """Separate fields into sensitive and non-sensitive categories.
        
        Args:
            data: Source DataFrame
            sensitivity_report: Sensitivity report with classifications
            
        Returns:
            Tuple of (sensitive_fields, non_sensitive_fields, sensitive_classifications)
        """
        sensitive_fields = []
        non_sensitive_fields = []
        sensitive_classifications = {}
        
        for field_name in data.columns:
            classification = sensitivity_report.classifications.get(field_name)
            
            if classification and classification.is_sensitive:
                sensitive_fields.append(field_name)
                sensitive_classifications[field_name] = classification
            else:
                non_sensitive_fields.append(field_name)
        
        logger.info(
            f"Separated fields: {len(sensitive_fields)} sensitive, "
            f"{len(non_sensitive_fields)} non-sensitive"
        )
        
        return sensitive_fields, non_sensitive_fields, sensitive_classifications
    
    def generate_synthetic_data(
        self,
        data: pd.DataFrame,
        sensitivity_report: SensitivityReport,
        num_rows: int,
        sdv_model: str = 'gaussian_copula',
        seed: Optional[int] = None,
        schema: Optional['DataSchema'] = None,
        referenced_data: Optional[Dict[str, pd.DataFrame]] = None,
        edge_case_rules: Optional[List[EdgeCaseRule]] = None,
        preserve_edge_cases: bool = True,
        edge_case_frequency: float = 0.05,
        field_strategies: Optional[Dict[str, Dict[str, Any]]] = None,
        **sdv_params
    ) -> SyntheticDataset:
        """Generate synthetic data using SDV for tabular structure.
        
        Args:
            data: Source production data
            sensitivity_report: Sensitivity report with field classifications
            num_rows: Number of synthetic rows to generate
            sdv_model: SDV model type ('gaussian_copula', 'ctgan', 'copula_gan')
            seed: Random seed for reproducibility
            schema: Optional DataSchema for constraint enforcement
            referenced_data: Optional dict mapping table names to DataFrames for FK resolution
            edge_case_rules: Optional list of EdgeCaseRules for edge case injection
            preserve_edge_cases: Whether to inject edge cases (default True)
            edge_case_frequency: Default frequency for edge case injection if no rules provided
            field_strategies: Optional dict mapping field names to strategy configurations
                Format: {
                    'field_name': {
                        'strategy': 'sdv' | 'bedrock_llm' | 'bedrock_examples',
                        'sdv_model': 'gaussian_copula' | 'ctgan' | None,
                        'custom_params': {...}  # For bedrock_examples: {'examples': [...]}
                    }
                }
            **sdv_params: Additional parameters for SDV synthesizer
            
        Returns:
            SyntheticDataset with generated data and quality metrics
        """
        logger.info(
            f"Starting synthetic data generation: {num_rows} rows, "
            f"model={sdv_model}, seed={seed}"
        )
        
        # Log data loading milestone
        if self.agent_logger:
            self.agent_logger.info(
                f"Data loading complete: {len(data)} rows, {len(data.columns)} columns",
                metadata={'source_rows': len(data), 'source_columns': len(data.columns)}
            )
        
        # Separate sensitive and non-sensitive fields
        sensitive_fields, non_sensitive_fields, sensitive_classifications = \
            self.separate_fields(data, sensitivity_report)
        
        # Log sensitivity analysis milestone
        if self.agent_logger:
            self.agent_logger.info(
                f"Sensitivity analysis complete: {len(sensitive_fields)} sensitive fields, {len(non_sensitive_fields)} non-sensitive fields",
                metadata={
                    'sensitive_count': len(sensitive_fields),
                    'non_sensitive_count': len(non_sensitive_fields),
                    'sensitive_fields': sensitive_fields
                }
            )
        
        # Initialize SDV wrapper
        self.sdv_wrapper = SDVSynthesizerWrapper(
            model_type=sdv_model,
            **sdv_params
        )
        
        # Determine which fields to generate with SDV vs Bedrock based on strategies
        bedrock_fields = []
        sdv_fields = list(data.columns)
        
        if field_strategies:
            # Separate fields based on user-selected strategies
            bedrock_fields = [
                field_name for field_name, strategy_config in field_strategies.items()
                if strategy_config.get('strategy') in ['bedrock_llm', 'bedrock_examples']
                and field_name in data.columns
            ]
            sdv_fields = [
                field_name for field_name in data.columns
                if field_name not in bedrock_fields
            ]
            
            logger.info(
                f"Strategy-based field separation: {len(bedrock_fields)} Bedrock fields, "
                f"{len(sdv_fields)} SDV fields"
            )
        
        # Log SDV model training milestone
        if self.agent_logger:
            self.agent_logger.info(
                f"Training SDV model: {sdv_model}",
                metadata={'model_type': sdv_model, 'model_params': sdv_params}
            )
        
        # Fit synthesizer on SDV fields only
        if sdv_fields:
            sdv_data = data[sdv_fields]
            # Create metadata only for SDV fields
            metadata = self.sdv_wrapper.create_metadata(sdv_data, sensitivity_report)
            self.sdv_wrapper.fit(sdv_data, metadata, seed=seed)
            
            # Generate synthetic data for SDV fields
            synthetic_df = self.sdv_wrapper.sample(num_rows=num_rows, seed=seed)
            
            # Log SDV generation complete
            if self.agent_logger:
                self.agent_logger.info(
                    f"SDV generation complete: {len(synthetic_df)} rows, {len(sdv_fields)} fields",
                    metadata={'generated_rows': len(synthetic_df), 'sdv_fields': sdv_fields}
                )
        else:
            # No SDV fields, create empty DataFrame with correct number of rows
            synthetic_df = pd.DataFrame(index=range(num_rows))
        
        # Generate Bedrock fields
        # Debug logging
        if self.agent_logger:
            self.agent_logger.info(
                f"Bedrock check: bedrock_client={self.bedrock_client is not None}, bedrock_fields={bedrock_fields}",
                metadata={'has_bedrock_client': self.bedrock_client is not None, 'bedrock_fields_list': bedrock_fields}
            )
        
        if self.bedrock_client and bedrock_fields:
            # Log Bedrock generation milestone
            if self.agent_logger:
                self.agent_logger.info(
                    f"Starting Bedrock generation for {len(bedrock_fields)} fields",
                    metadata={'bedrock_fields': bedrock_fields}
                )
            
            synthetic_df = self._generate_bedrock_fields(
                synthetic_df=synthetic_df,
                data=data,
                bedrock_fields=bedrock_fields,
                field_strategies=field_strategies,
                seed=seed
            )
            
            # Log Bedrock generation complete
            if self.agent_logger:
                self.agent_logger.info(
                    f"Bedrock generation complete for {len(bedrock_fields)} fields",
                    metadata={'fields_processed': len(bedrock_fields)}
                )
        
        # Enforce schema constraints if provided
        if schema is not None:
            synthetic_df = self._enforce_schema_constraints(synthetic_df, schema, referenced_data)
        
        # Inject edge cases if enabled
        edge_case_result = None
        if preserve_edge_cases:
            synthetic_df, edge_case_result = self._inject_edge_cases(
                synthetic_df=synthetic_df,
                edge_case_rules=edge_case_rules,
                edge_case_frequency=edge_case_frequency,
                seed=seed
            )
        
        # Reorder columns to match original data order from sensitivity report
        # Do this BEFORE quality evaluation so validation sees correct order
        # Use sensitivity_report.column_order if available, otherwise fall back to data.columns
        if sensitivity_report.column_order:
            original_columns = sensitivity_report.column_order
            logger.info(f"Using column order from sensitivity report: {original_columns}")
        else:
            original_columns = list(data.columns)
            logger.warning(
                "No column order in sensitivity report, using data.columns order. "
                "This may indicate an older sensitivity report format."
            )
        
        # Validate that data columns match expected order
        if list(data.columns) != original_columns:
            logger.warning(
                f"Column order mismatch detected between data and sensitivity report. "
                f"Expected: {original_columns}, Got: {list(data.columns)}"
            )
        
        # Enforce column order on synthetic data
        synthetic_df = self._enforce_column_order(synthetic_df, original_columns)
        
        # Evaluate quality AFTER column order enforcement
        quality_metrics = self._evaluate_quality(data, synthetic_df, edge_case_result)
        
        # Remove edge case tag column from final output (keep it internal)
        if '_edge_case_tags' in synthetic_df.columns:
            # Store tags in metadata before removing
            edge_case_tags = synthetic_df['_edge_case_tags'].tolist()
            if edge_case_result:
                edge_case_result.edge_case_tags_full = edge_case_tags
            synthetic_df = synthetic_df.drop(columns=['_edge_case_tags'])
        
        # Determine generation method description
        if bedrock_fields and sdv_fields:
            generation_method = f"Hybrid (Bedrock: {len(bedrock_fields)} fields, SDV: {len(sdv_fields)} fields)"
        elif bedrock_fields:
            generation_method = f"Bedrock only ({len(bedrock_fields)} fields)"
        elif sdv_fields:
            generation_method = f"SDV only ({len(sdv_fields)} fields)"
        else:
            generation_method = "Unknown"
        
        # Create generation metadata
        generation_metadata = {
            'sdv_model': sdv_model,
            'sdv_params': sdv_params,
            'source_rows': len(data),
            'generated_rows': len(synthetic_df),
            'sensitive_fields': sensitive_fields,
            'non_sensitive_fields': non_sensitive_fields,
            'generation_timestamp': datetime.now().isoformat(),
            'edge_cases_injected': edge_case_result is not None,
            'edge_case_injection_result': edge_case_result.to_dict() if edge_case_result else None,
            'generation_method': generation_method,
            'bedrock_fields': bedrock_fields,
            'sdv_fields': sdv_fields,
            'original_column_order': original_columns,
            'final_column_order': list(synthetic_df.columns),
            'column_order_preserved': quality_metrics.column_order_preserved
        }
        
        # Create SyntheticDataset
        synthetic_dataset = SyntheticDataset(
            data=synthetic_df,
            quality_metrics=quality_metrics,
            generation_metadata=generation_metadata,
            generation_method=generation_method,
            timestamp=datetime.now(),
            seed=seed,
            num_records=len(synthetic_df)
        )
        
        logger.info(
            f"Synthetic data generation complete. "
            f"Quality score: {quality_metrics.sdv_quality_score:.3f}"
        )
        
        # Log completion milestone
        if self.agent_logger:
            self.agent_logger.info(
                f"Synthetic data generation complete: {len(synthetic_df)} rows, quality score: {quality_metrics.sdv_quality_score:.3f}",
                metadata={
                    'total_rows': len(synthetic_df),
                    'quality_score': quality_metrics.sdv_quality_score,
                    'edge_cases_injected': edge_case_result is not None
                }
            )
        
        return synthetic_dataset
    
    def _inject_edge_cases(
        self,
        synthetic_df: pd.DataFrame,
        edge_case_rules: Optional[List[EdgeCaseRule]],
        edge_case_frequency: float,
        seed: Optional[int]
    ) -> tuple[pd.DataFrame, Any]:
        """Inject edge cases into synthetic data.
        
        Args:
            synthetic_df: Synthetic DataFrame
            edge_case_rules: Optional list of EdgeCaseRules
            edge_case_frequency: Default frequency if no rules provided
            seed: Random seed for reproducibility
            
        Returns:
            Tuple of (modified DataFrame, EdgeCaseInjectionResult)
        """
        # If no rules provided, create default rules for common fields
        if edge_case_rules is None:
            edge_case_rules = self._create_default_edge_case_rules(
                synthetic_df, edge_case_frequency
            )
        
        if not edge_case_rules:
            logger.info("No edge case rules to apply")
            return synthetic_df, None
        
        # Inject edge cases
        result_df, injection_result = self.edge_case_generator.inject_edge_cases(
            data=synthetic_df,
            rules=edge_case_rules,
            seed=seed
        )
        
        return result_df, injection_result
    
    def _enforce_column_order(
        self,
        df: pd.DataFrame,
        target_order: List[str]
    ) -> pd.DataFrame:
        """Enforce specific column order on DataFrame.
        
        Args:
            df: DataFrame to reorder
            target_order: Desired column order
            
        Returns:
            DataFrame with columns in target order
        """
        # Get columns that exist in both df and target_order
        existing_columns = [col for col in target_order if col in df.columns]
        
        # Get any extra columns not in target_order (shouldn't happen)
        extra_columns = [col for col in df.columns if col not in target_order]
        
        if extra_columns:
            logger.warning(
                f"Found unexpected columns not in original order: {extra_columns}. "
                f"These will be appended to the end."
            )
        
        # Check for missing columns
        missing_columns = [col for col in target_order if col not in df.columns]
        if missing_columns:
            logger.warning(
                f"Expected columns not found in DataFrame: {missing_columns}"
            )
        
        # Reorder DataFrame
        reordered_df = df[existing_columns + extra_columns]
        logger.info(f"Enforced column order: {list(reordered_df.columns)}")
        
        return reordered_df
    
    def _create_default_edge_case_rules(
        self,
        data: pd.DataFrame,
        frequency: float
    ) -> List[EdgeCaseRule]:
        """Create default edge case rules based on field names and types.
        
        Args:
            data: DataFrame to create rules for
            frequency: Default frequency for edge cases
            
        Returns:
            List of EdgeCaseRules
        """
        rules = []
        
        for column in data.columns:
            # Skip the edge case tag column
            if column == '_edge_case_tags':
                continue
            
            # Infer field type from column name
            column_lower = column.lower()
            
            # Email fields
            if 'email' in column_lower or 'e_mail' in column_lower:
                rules.append(EdgeCaseRule(
                    field_name=column,
                    edge_case_types=[
                        EdgeCaseType.MALFORMED_EMAIL,
                        EdgeCaseType.EMPTY_STRING,
                        EdgeCaseType.NULL_VALUE
                    ],
                    frequency=frequency,
                    field_type='email'
                ))
            
            # Phone fields
            elif 'phone' in column_lower or 'tel' in column_lower or 'mobile' in column_lower:
                rules.append(EdgeCaseRule(
                    field_name=column,
                    edge_case_types=[
                        EdgeCaseType.MALFORMED_PHONE,
                        EdgeCaseType.EMPTY_STRING,
                        EdgeCaseType.NULL_VALUE
                    ],
                    frequency=frequency,
                    field_type='phone'
                ))
            
            # Postcode/ZIP fields
            elif any(x in column_lower for x in ['postcode', 'postal', 'zip', 'zipcode']):
                rules.append(EdgeCaseRule(
                    field_name=column,
                    edge_case_types=[
                        EdgeCaseType.INVALID_POSTCODE,
                        EdgeCaseType.EMPTY_STRING,
                        EdgeCaseType.NULL_VALUE
                    ],
                    frequency=frequency,
                    field_type='postcode'
                ))
            
            # Numeric fields
            elif pd.api.types.is_numeric_dtype(data[column]):
                rules.append(EdgeCaseRule(
                    field_name=column,
                    edge_case_types=[
                        EdgeCaseType.NEGATIVE_VALUE,
                        EdgeCaseType.ZERO_VALUE,
                        EdgeCaseType.NULL_VALUE
                    ],
                    frequency=frequency,
                    field_type='number'
                ))
            
            # String fields
            elif pd.api.types.is_string_dtype(data[column]) or pd.api.types.is_object_dtype(data[column]):
                rules.append(EdgeCaseRule(
                    field_name=column,
                    edge_case_types=[
                        EdgeCaseType.EMPTY_STRING,
                        EdgeCaseType.WHITESPACE_ONLY,
                        EdgeCaseType.NULL_VALUE,
                        EdgeCaseType.SPECIAL_CHARACTERS
                    ],
                    frequency=frequency,
                    field_type='string'
                ))
        
        logger.info(f"Created {len(rules)} default edge case rules")
        return rules
    
    def _evaluate_quality(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        edge_case_result: Optional[Any] = None
    ) -> QualityMetrics:
        """Evaluate quality of synthetic data.
        
        Args:
            real_data: Original data
            synthetic_data: Generated synthetic data
            edge_case_result: Optional edge case injection result
            
        Returns:
            QualityMetrics object
        """
        # Remove edge case tag column if present (not part of original schema)
        synthetic_data_for_eval = synthetic_data.copy()
        if '_edge_case_tags' in synthetic_data_for_eval.columns:
            synthetic_data_for_eval = synthetic_data_for_eval.drop(columns=['_edge_case_tags'])
        
        # Get SDV quality metrics only for fields that were generated with SDV
        # (SDV wrapper metadata only contains SDV fields)
        if self.sdv_wrapper.metadata is not None:
            sdv_field_names = list(self.sdv_wrapper.metadata.columns.keys())
            # Filter to only SDV fields for evaluation
            real_data_sdv = real_data[sdv_field_names]
            synthetic_data_sdv = synthetic_data_for_eval[sdv_field_names]
            sdv_metrics = self.sdv_wrapper.evaluate_quality(real_data_sdv, synthetic_data_sdv)
        else:
            # No SDV fields, use default metrics
            sdv_metrics = {
                'overall_quality_score': 1.0,
                'column_shapes': {},
                'column_pair_trends': {}
            }
        
        # Extract scores
        overall_score = sdv_metrics['overall_quality_score']
        
        # Get column shapes and column pair trends scores
        column_shapes_details = sdv_metrics.get('column_shapes', {})
        column_pair_trends_details = sdv_metrics.get('column_pair_trends', {})
        
        # Calculate average scores from details
        column_shapes_score = self._calculate_average_score(column_shapes_details)
        column_pair_trends_score = self._calculate_average_score(column_pair_trends_details)
        
        # Perform statistical tests
        ks_tests = self._perform_ks_tests(real_data, synthetic_data_for_eval)
        
        # Calculate correlation preservation
        correlation_preservation = self._calculate_correlation_preservation(
            real_data, synthetic_data_for_eval
        )
        
        # Calculate edge case frequency match
        edge_case_frequency_match = self._calculate_edge_case_frequency_match(
            real_data, synthetic_data_for_eval, edge_case_result
        )
        
        # Extract per-field scores
        field_scores = {}
        if isinstance(column_shapes_details, dict):
            for field, details in column_shapes_details.items():
                if isinstance(details, dict) and 'score' in details:
                    field_scores[field] = details['score']
        
        # Validate column order
        column_order_report = validate_column_order(
            original_columns=list(real_data.columns),
            synthetic_columns=list(synthetic_data_for_eval.columns)
        )
        column_order_preserved = column_order_report['order_preserved']
        
        # Run diagnostic evaluation for data validity and structure
        diagnostic_details = {}
        data_validity_score = 0.0
        data_structure_score = 0.0
        
        try:
            if self.sdv_wrapper.metadata is not None and len(sdv_field_names) > 0:
                logger.info("Running SDV diagnostic evaluation...")
                diagnostic_report = run_diagnostic(
                    real_data=real_data_sdv,
                    synthetic_data=synthetic_data_sdv,
                    metadata=self.sdv_wrapper.metadata,
                    verbose=False
                )
                
                # Extract diagnostic scores
                data_validity_score = diagnostic_report.get_score()
                diagnostic_details = diagnostic_report.get_details()
                
                # Get structure score from properties
                properties = diagnostic_report.get_properties()
                data_structure_score = properties.get('Score', data_validity_score)
                
                logger.info(f"Diagnostic scores - Validity: {data_validity_score:.3f}, Structure: {data_structure_score:.3f}")
        except Exception as e:
            logger.warning(f"Failed to run diagnostic evaluation: {e}")
        
        # Calculate privacy metrics (nearest neighbor distances for data leakage detection)
        nearest_neighbor_distances = self._calculate_nearest_neighbor_distances(
            real_data, synthetic_data_for_eval
        )
        
        return QualityMetrics(
            sdv_quality_score=overall_score,
            column_shapes_score=column_shapes_score,
            column_pair_trends_score=column_pair_trends_score,
            ks_tests=ks_tests,
            correlation_preservation=correlation_preservation,
            edge_case_frequency_match=edge_case_frequency_match,
            field_scores=field_scores,
            column_order_preserved=column_order_preserved,
            column_order_report=column_order_report,
            data_validity_score=data_validity_score,
            data_structure_score=data_structure_score,
            diagnostic_details=diagnostic_details,
            nearest_neighbor_distances=nearest_neighbor_distances
        )
    
    def _calculate_average_score(self, details: Any) -> float:
        """Calculate average score from SDV details.
        
        Args:
            details: SDV quality details (can be dict, DataFrame, or other)
            
        Returns:
            Average score as float
        """
        if isinstance(details, dict):
            # If it's a dict with 'score' key
            if 'score' in details:
                return float(details['score'])
            # If it's a dict of field scores
            scores = []
            for value in details.values():
                if isinstance(value, (int, float)):
                    scores.append(float(value))
                elif isinstance(value, dict) and 'score' in value:
                    scores.append(float(value['score']))
            return np.mean(scores) if scores else 0.0
        elif isinstance(details, pd.DataFrame):
            # If it's a DataFrame with a 'Score' column
            if 'Score' in details.columns:
                return float(details['Score'].mean())
            # Try to find numeric columns
            numeric_cols = details.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                return float(details[numeric_cols].mean().mean())
        
        # Default to 0.0 if we can't extract a score
        return 0.0
    
    def _perform_ks_tests(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """Perform Kolmogorov-Smirnov tests on numeric columns.
        
        Args:
            real_data: Original data
            synthetic_data: Generated synthetic data
            
        Returns:
            Dictionary mapping column names to KS test results
        """
        from scipy.stats import ks_2samp
        
        ks_tests = {}
        
        # Get numeric columns
        numeric_columns = real_data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if column not in synthetic_data.columns:
                continue
            
            # Get non-null values
            real_values = real_data[column].dropna()
            synth_values = synthetic_data[column].dropna()
            
            if len(real_values) > 0 and len(synth_values) > 0:
                try:
                    statistic, pvalue = ks_2samp(real_values, synth_values)
                    ks_tests[column] = {
                        'statistic': float(statistic),
                        'pvalue': float(pvalue)
                    }
                except Exception as e:
                    logger.warning(f"KS test failed for column {column}: {e}")
        
        return ks_tests
    
    def _calculate_correlation_preservation(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> float:
        """Calculate how well correlations are preserved.
        
        Args:
            real_data: Original data
            synthetic_data: Generated synthetic data
            
        Returns:
            Correlation preservation score (0-1, higher is better)
        """
        # Get numeric columns present in both datasets
        numeric_columns = real_data.select_dtypes(include=[np.number]).columns
        common_numeric = [col for col in numeric_columns if col in synthetic_data.columns]
        
        if len(common_numeric) < 2:
            # Need at least 2 numeric columns for correlation
            return 1.0
        
        try:
            # Calculate correlation matrices
            real_corr = real_data[common_numeric].corr()
            synth_corr = synthetic_data[common_numeric].corr()
            
            # Calculate mean absolute difference
            corr_diff = np.abs(real_corr - synth_corr)
            
            # Remove diagonal (self-correlation)
            np.fill_diagonal(corr_diff.values, 0)
            
            # Calculate preservation score (1 - mean difference)
            mean_diff = corr_diff.values[np.triu_indices_from(corr_diff.values, k=1)].mean()
            preservation_score = 1.0 - mean_diff
            
            return float(max(0.0, preservation_score))
        except Exception as e:
            logger.warning(f"Correlation preservation calculation failed: {e}")
            return 0.0
    
    def _calculate_nearest_neighbor_distances(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate nearest neighbor distances for privacy/data leakage detection.
        
        For each synthetic record, find the distance to its nearest neighbor in the real data.
        Small distances indicate potential data leakage (synthetic data too similar to real data).
        
        Args:
            real_data: Original data
            synthetic_data: Synthetic data
            
        Returns:
            Dictionary with distance statistics
        """
        try:
            from scipy.spatial.distance import cdist
            
            # Only use numeric columns for distance calculation
            numeric_cols = real_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return {'error': 'No numeric columns for distance calculation'}
            
            # Normalize data for fair distance calculation
            real_numeric = real_data[numeric_cols].fillna(0)
            synth_numeric = synthetic_data[numeric_cols].fillna(0)
            
            # Standardize (mean=0, std=1)
            means = real_numeric.mean()
            stds = real_numeric.std().replace(0, 1)  # Avoid division by zero
            
            real_normalized = (real_numeric - means) / stds
            synth_normalized = (synth_numeric - means) / stds
            
            # Calculate pairwise distances (limit to first 1000 rows for performance)
            max_rows = min(1000, len(synth_normalized))
            distances = cdist(
                synth_normalized.iloc[:max_rows].values,
                real_normalized.values,
                metric='euclidean'
            )
            
            # Find minimum distance for each synthetic record
            min_distances = distances.min(axis=1)
            
            # Calculate statistics
            return {
                'mean_distance': float(np.mean(min_distances)),
                'median_distance': float(np.median(min_distances)),
                'min_distance': float(np.min(min_distances)),
                'max_distance': float(np.max(min_distances)),
                'std_distance': float(np.std(min_distances)),
                'samples_evaluated': max_rows,
                'interpretation': 'Higher distances indicate better privacy (less data leakage)'
            }
        except Exception as e:
            logger.warning(f"Failed to calculate nearest neighbor distances: {e}")
            return {'error': str(e)}
    
    def _calculate_edge_case_frequency_match(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        edge_case_result: Optional[Any] = None
    ) -> float:
        """Calculate how well edge case frequencies match between real and synthetic data.
        
        Args:
            real_data: Original data
            synthetic_data: Generated synthetic data
            edge_case_result: Optional EdgeCaseInjectionResult
            
        Returns:
            Edge case frequency match score (0-1, higher is better)
        """
        if edge_case_result is None:
            # No edge cases were injected, return perfect score
            return 1.0
        
        # For now, we'll use a simple metric: if edge cases were injected,
        # check if the frequency is close to what was requested
        # In a full implementation, this would compare actual data quality issues
        # in production data vs synthetic data
        
        # If we have the injection result, we know the achieved frequency
        # We consider it a good match if edge cases were successfully injected
        if hasattr(edge_case_result, 'frequency_achieved'):
            # If edge cases were injected, return a score based on whether
            # the frequency is reasonable (> 0)
            if edge_case_result.frequency_achieved > 0:
                return 1.0
            else:
                return 0.5
        
        return 1.0
    
    def _generate_bedrock_fields(
        self,
        synthetic_df: pd.DataFrame,
        data: pd.DataFrame,
        bedrock_fields: List[str],
        field_strategies: Optional[Dict[str, Dict[str, Any]]] = None,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """Generate values for fields using Bedrock based on their strategies.
        
        Args:
            synthetic_df: Synthetic DataFrame (may be empty or partial)
            data: Original data for context
            bedrock_fields: List of field names to generate with Bedrock
            field_strategies: Dict mapping field names to strategy configurations
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with Bedrock-generated fields added
        """
        if seed is not None:
            np.random.seed(seed)
        
        num_rows = len(synthetic_df) if len(synthetic_df) > 0 else len(data)
        
        for field_name in bedrock_fields:
            if field_name not in data.columns:
                continue
            
            strategy_config = field_strategies.get(field_name, {}) if field_strategies else {}
            strategy_type = strategy_config.get('strategy', 'bedrock_llm')
            
            try:
                logger.info(f"Generating {num_rows} values for field '{field_name}' using {strategy_type}")
                
                # Use fallback generator as the fallback function
                def fallback_fn(field_name, field_type, num_values):
                    return self.fallback_generator.generate(
                        field_name=field_name,
                        field_type=field_type or 'string',
                        num_values=num_values
                    )
                
                # Check if using bedrock_examples strategy
                if strategy_type == 'bedrock_examples':
                    custom_params = strategy_config.get('custom_params', {})
                    examples = custom_params.get('examples', [])
                    
                    # Handle examples as string (newline-separated) or list
                    if isinstance(examples, str):
                        examples = [ex.strip() for ex in examples.split('\n') if ex.strip()]
                    
                    if not examples or len(examples) < 3:
                        logger.warning(
                            f"Field '{field_name}' uses bedrock_examples but has insufficient examples ({len(examples)}). "
                            "Falling back to standard generation."
                        )
                        # Fall through to standard generation
                        strategy_type = 'bedrock_llm'
                    else:
                        if self.agent_logger:
                            self.agent_logger.info(
                                f"Generating field '{field_name}' with {len(examples)} examples",
                                metadata={
                                    'field_name': field_name,
                                    'num_examples': len(examples),
                                    'num_values': num_rows
                                }
                            )
                        
                        generated_values = self.bedrock_client.generate_from_examples(
                            field_name=field_name,
                            examples=examples,
                            num_values=num_rows,
                            fallback_generator=fallback_fn
                        )
                        
                        synthetic_df[field_name] = generated_values[:num_rows]
                        logger.info(f"Successfully generated field '{field_name}' using examples")
                        continue
                
                # Standard Bedrock LLM generation
                # Infer field type from data
                field_type = 'string'
                if pd.api.types.is_numeric_dtype(data[field_name]):
                    field_type = 'number'
                elif pd.api.types.is_datetime64_any_dtype(data[field_name]):
                    field_type = 'date'
                
                if self.agent_logger:
                    self.agent_logger.info(
                        f"Generating field '{field_name}' with Bedrock LLM",
                        metadata={'field_name': field_name, 'field_type': field_type, 'num_values': num_rows}
                    )
                
                generated_values = self.bedrock_client.generate_text_field(
                    field_name=field_name,
                    field_type=field_type,
                    num_values=num_rows,
                    context={},
                    constraints=None,
                    fallback_generator=fallback_fn
                )
                
                synthetic_df[field_name] = generated_values[:num_rows]
                logger.info(f"Successfully generated field '{field_name}' with Bedrock")
                
            except Exception as e:
                logger.error(f"Failed to generate field '{field_name}' with Bedrock: {e}")
                
                if self.agent_logger:
                    self.agent_logger.log_warning(
                        f"Bedrock generation failed for '{field_name}', using fallback",
                        metadata={'field_name': field_name, 'error': str(e)}
                    )
                
                # Use fallback generator
                try:
                    fallback_values = self.fallback_generator.generate(
                        field_name=field_name,
                        field_type='string',
                        num_values=num_rows
                    )
                    synthetic_df[field_name] = fallback_values
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for '{field_name}': {fallback_error}")
        
        return synthetic_df
    
    def _replace_sensitive_text_fields(
        self,
        synthetic_df: pd.DataFrame,
        sensitive_classifications: Dict[str, FieldClassification],
        context_data: Optional[pd.DataFrame] = None,
        seed: Optional[int] = None,
        field_strategies: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> pd.DataFrame:
        """Replace sensitive text fields with Bedrock-generated values.
        
        Args:
            synthetic_df: Synthetic DataFrame with SDV-generated values
            sensitive_classifications: Dictionary of sensitive field classifications
            context_data: Optional context data from non-sensitive fields
            seed: Random seed for reproducibility
            field_strategies: Optional dict mapping field names to strategy configurations
            
        Returns:
            DataFrame with sensitive fields replaced
        """
        logger.info(
            f"Replacing {len(sensitive_classifications)} sensitive text fields "
            "with Bedrock-generated values"
        )
        
        # Set random seed for reproducibility
        if seed is not None:
            np.random.seed(seed)
        
        # Prepare context from non-sensitive fields
        context = {}
        if context_data is not None and not context_data.empty:
            for col in context_data.columns:
                # Get sample values for context
                sample_values = context_data[col].dropna().head(5).tolist()
                if sample_values:
                    context[col] = sample_values
        
        # Process each sensitive field
        for field_name, classification in sensitive_classifications.items():
            if field_name not in synthetic_df.columns:
                continue
            
            # Check if field has a specific strategy
            field_strategy = field_strategies.get(field_name) if field_strategies else None
            strategy_type = field_strategy.get('strategy') if field_strategy else None
            
            # Skip if strategy is explicitly set to 'sdv'
            if strategy_type == 'sdv':
                logger.debug(f"Skipping field '{field_name}' - using SDV strategy")
                continue
            
            # Only replace text-based sensitive fields
            # Structured fields (like SSN, credit card) are better handled by rules
            text_types = ['name', 'first_name', 'last_name', 'email', 'address', 
                         'street_address', 'city', 'company', 'job', 'description']
            
            if classification.sensitivity_type not in text_types:
                logger.debug(
                    f"Skipping field '{field_name}' (type: {classification.sensitivity_type}), "
                    "not a text-based field"
                )
                continue
            
            try:
                # Generate replacement values using Bedrock
                num_values = len(synthetic_df)
                
                logger.info(
                    f"Generating {num_values} values for sensitive field '{field_name}' "
                    f"(type: {classification.sensitivity_type}, strategy: {strategy_type or 'bedrock_llm'})"
                )
                
                # Log batch processing progress
                if self.agent_logger:
                    self.agent_logger.log_info(
                        f"Processing batch for field '{field_name}': {num_values} values",
                        metadata={
                            'field_name': field_name,
                            'field_type': classification.sensitivity_type,
                            'batch_size': num_values,
                            'strategy': strategy_type or 'bedrock_llm'
                        }
                    )
                
                # Use fallback generator as the fallback function
                def fallback_fn(field_name, field_type, num_values):
                    return self.fallback_generator.generate(
                        field_name=field_name,
                        field_type=field_type,
                        num_values=num_values
                    )
                
                # Check if using bedrock_examples strategy
                if strategy_type == 'bedrock_examples':
                    # Extract examples from custom_params
                    custom_params = field_strategy.get('custom_params', {})
                    examples = custom_params.get('examples', [])
                    
                    if not examples:
                        logger.warning(
                            f"Field '{field_name}' uses bedrock_examples strategy but no examples provided. "
                            "Falling back to standard generation."
                        )
                        # Fall through to standard generation
                    else:
                        # Log API call attempt
                        if self.agent_logger:
                            self.agent_logger.log_info(
                                f"Calling Bedrock API with examples for field '{field_name}'",
                                metadata={
                                    'field_name': field_name,
                                    'num_values': num_values,
                                    'num_examples': len(examples)
                                }
                            )
                        
                        # Use generate_from_examples method
                        generated_values = self.bedrock_client.generate_from_examples(
                            field_name=field_name,
                            examples=examples,
                            num_values=num_values,
                            fallback_generator=fallback_fn
                        )
                        
                        # Replace values in DataFrame
                        synthetic_df[field_name] = generated_values[:num_values]
                        
                        logger.info(f"Successfully replaced field '{field_name}' using examples")
                        continue
                
                # Standard Bedrock LLM generation
                # Log API call attempt
                if self.agent_logger:
                    self.agent_logger.log_info(
                        f"Calling Bedrock API for field '{field_name}'",
                        metadata={'field_name': field_name, 'num_values': num_values}
                    )
                
                # Generate values with Bedrock (with fallback)
                generated_values = self.bedrock_client.generate_text_field(
                    field_name=field_name,
                    field_type=classification.sensitivity_type,
                    num_values=num_values,
                    context=context,
                    constraints=None,  # Could be extracted from classification
                    fallback_generator=fallback_fn
                )
                
                # Replace values in DataFrame
                synthetic_df[field_name] = generated_values[:num_values]
                
                logger.info(f"Successfully replaced field '{field_name}'")
                
            except Exception as e:
                logger.error(
                    f"Failed to replace sensitive field '{field_name}': {e}, "
                    "using fallback generator"
                )
                
                # Log retry attempt
                if self.agent_logger:
                    self.agent_logger.log_warning(
                        f"Bedrock API failed for field '{field_name}', retrying with fallback generator",
                        metadata={'field_name': field_name, 'error': str(e)}
                    )
                
                # Use fallback generator directly
                try:
                    fallback_values = self.fallback_generator.generate(
                        field_name=field_name,
                        field_type=classification.sensitivity_type,
                        num_values=len(synthetic_df)
                    )
                    synthetic_df[field_name] = fallback_values
                    logger.info(f"Used fallback generator for field '{field_name}'")
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback generation also failed for '{field_name}': {fallback_error}"
                    )
                    # Keep SDV-generated values as last resort
        
        return synthetic_df
    
    def _enforce_schema_constraints(
        self,
        synthetic_df: pd.DataFrame,
        schema: 'DataSchema',
        referenced_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> pd.DataFrame:
        """Enforce schema constraints on generated synthetic data.
        
        Args:
            synthetic_df: Generated synthetic data
            schema: DataSchema with constraints to enforce
            referenced_data: Optional dict mapping table names to their DataFrames for FK resolution
            
        Returns:
            DataFrame with constraints enforced
        """
        from shared.models.schema import ConstraintType
        
        logger.info("Enforcing schema constraints on synthetic data")
        
        # Get the table schema
        if not schema.tables:
            return synthetic_df
        
        # Find the table that matches the columns in synthetic_df
        # Try to match by checking if table fields match dataframe columns
        table = None
        for t in schema.tables:
            table_field_names = {f.name for f in t.fields}
            df_columns = set(synthetic_df.columns)
            # If most columns match, this is probably the right table
            if len(table_field_names & df_columns) / len(df_columns) > 0.5:
                table = t
                break
        
        if table is None:
            # Fallback to first table
            table = schema.tables[0]
            logger.warning(
                f"Could not find matching table schema for DataFrame with columns {list(synthetic_df.columns)[:5]}. "
                f"Using first table: {table.name}"
            )
        
        # Create a copy to avoid modifying the original
        result_df = synthetic_df.copy()
        
        # Enforce constraints for each field
        for field in table.fields:
            if field.name not in result_df.columns:
                continue
            
            column_data = result_df[field.name]
            
            # Process each constraint
            for constraint in field.constraints:
                if constraint.type == ConstraintType.RANGE:
                    # Clip values to range
                    min_val = constraint.params.get('min')
                    max_val = constraint.params.get('max')
                    
                    if min_val is not None:
                        column_data = column_data.clip(lower=min_val)
                    if max_val is not None:
                        column_data = column_data.clip(upper=max_val)
                    
                    result_df[field.name] = column_data
                
                elif constraint.type == ConstraintType.LENGTH:
                    # Truncate or pad strings to meet length constraints
                    min_len = constraint.params.get('min')
                    max_len = constraint.params.get('max')
                    
                    def enforce_length(val):
                        if pd.isna(val):
                            return val
                        s = str(val)
                        if max_len is not None and len(s) > max_len:
                            s = s[:max_len]
                        if min_len is not None and len(s) < min_len:
                            s = s.ljust(min_len, 'X')
                        return s
                    
                    result_df[field.name] = column_data.apply(enforce_length)
                
                elif constraint.type == ConstraintType.PATTERN:
                    # For pattern constraints, we can't easily fix values
                    # Log a warning if values don't match
                    pattern = constraint.params.get('pattern')
                    if pattern:
                        import re
                        pattern_re = re.compile(pattern)
                        non_matching = column_data[~column_data.astype(str).str.match(pattern_re, na=False)]
                        if len(non_matching) > 0:
                            logger.warning(
                                f"Field '{field.name}': {len(non_matching)} values don't match pattern '{pattern}'. "
                                f"Consider adjusting generation strategy."
                            )
                
                elif constraint.type == ConstraintType.ENUM:
                    # Replace invalid values with random valid values
                    allowed_values = constraint.params.get('values', [])
                    if allowed_values:
                        invalid_mask = ~column_data.isin(allowed_values)
                        num_invalid = invalid_mask.sum()
                        if num_invalid > 0:
                            # Replace with random valid values
                            replacements = np.random.choice(allowed_values, size=num_invalid)
                            result_df.loc[invalid_mask, field.name] = replacements
                
                elif constraint.type == ConstraintType.FOREIGN_KEY:
                    # Enforce referential integrity by replacing FK values with valid PK values
                    target_table = constraint.params.get('target_table')
                    target_field = constraint.params.get('target_field')
                    
                    if not target_table or not target_field:
                        logger.warning(
                            f"Foreign key constraint on '{field.name}' missing target_table or target_field"
                        )
                        continue
                    
                    # Check if we have the referenced data
                    if referenced_data and target_table in referenced_data:
                        referenced_df = referenced_data[target_table]
                        
                        if target_field in referenced_df.columns:
                            # Get valid primary key values from referenced table
                            valid_pk_values = referenced_df[target_field].dropna().unique()
                            
                            if len(valid_pk_values) == 0:
                                logger.warning(
                                    f"No valid primary key values found in {target_table}.{target_field}"
                                )
                                continue
                            
                            # Replace all FK values with random valid PK values
                            # This ensures referential integrity
                            num_rows = len(result_df)
                            new_fk_values = np.random.choice(valid_pk_values, size=num_rows)
                            result_df[field.name] = new_fk_values
                            
                            logger.info(
                                f"Enforced referential integrity for '{field.name}' -> "
                                f"{target_table}.{target_field} ({len(valid_pk_values)} valid values)"
                            )
                        else:
                            logger.warning(
                                f"Target field '{target_field}' not found in referenced table '{target_table}'"
                            )
                    elif target_table == table.name:
                        # Self-referencing foreign key
                        # Get valid primary key values from the same table
                        if target_field in result_df.columns:
                            valid_pk_values = result_df[target_field].dropna().unique()
                            
                            if len(valid_pk_values) == 0:
                                logger.warning(
                                    f"No valid primary key values found for self-reference in {field.name}"
                                )
                                continue
                            
                            # For self-references, we need to be careful about nulls
                            # Replace non-null FK values with random valid PK values
                            non_null_mask = result_df[field.name].notna()
                            num_non_null = non_null_mask.sum()
                            
                            if num_non_null > 0:
                                new_fk_values = np.random.choice(valid_pk_values, size=num_non_null)
                                result_df.loc[non_null_mask, field.name] = new_fk_values
                            
                            logger.info(
                                f"Enforced self-referential integrity for '{field.name}' -> "
                                f"{target_table}.{target_field} ({len(valid_pk_values)} valid values)"
                            )
                        else:
                            logger.warning(
                                f"Target field '{target_field}' not found in table '{table.name}'"
                            )
                    else:
                        logger.warning(
                            f"Referenced data for table '{target_table}' not provided for FK constraint on '{field.name}'"
                        )
                
                elif constraint.type == ConstraintType.REQUIRED:
                    # Fill null values with appropriate defaults
                    if column_data.isna().any():
                        if field.data_type.value in ['integer', 'float']:
                            # Use median for numeric fields
                            fill_value = column_data.median()
                        elif field.data_type.value == 'string':
                            # Use most common value for strings
                            fill_value = column_data.mode()[0] if len(column_data.mode()) > 0 else 'UNKNOWN'
                        else:
                            fill_value = column_data.mode()[0] if len(column_data.mode()) > 0 else None
                        
                        if fill_value is not None:
                            result_df[field.name] = column_data.fillna(fill_value)
        
        logger.info("Schema constraints enforced successfully")
        return result_df
    
    def save_synthetic_data(
        self,
        synthetic_dataset: SyntheticDataset,
        output_path: Path,
        format: str = 'csv'
    ):
        """Save synthetic data to file.
        
        Args:
            synthetic_dataset: SyntheticDataset to save
            output_path: Output file path
            format: Output format ('csv', 'json', 'parquet')
        """
        logger.info(f"Saving synthetic data to {output_path} in {format} format")
        
        if format == 'csv':
            synthetic_dataset.data.to_csv(output_path, index=False)
        elif format == 'json':
            synthetic_dataset.data.to_json(output_path, orient='records', indent=2)
        elif format == 'parquet':
            synthetic_dataset.data.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Also save metadata
        metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(synthetic_dataset.to_dict(include_data=False), f, indent=2)
        
        logger.info(f"Synthetic data and metadata saved successfully")
