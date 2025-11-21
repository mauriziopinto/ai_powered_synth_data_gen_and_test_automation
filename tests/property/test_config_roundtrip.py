"""Property-based tests for configuration serialization.

This module tests the round-trip property of workflow configurations:
saving and loading should preserve all configuration data.
"""

import json
from datetime import datetime
from pathlib import Path
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
import pytest

from shared.models.workflow import WorkflowConfig, TargetConfig


# Custom strategies for generating test data
@composite
def target_config_strategy(draw):
    """Generate a valid TargetConfig."""
    target_type = draw(st.sampled_from(['database', 'salesforce', 'api', 'file']))
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters=' -_'
    )))
    
    # Generate optional fields
    connection_string = draw(st.one_of(
        st.none(),
        st.text(min_size=10, max_size=100)
    ))
    
    credentials = draw(st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        )
    ))
    
    load_strategy = draw(st.sampled_from(['truncate_insert', 'upsert']))
    
    table_mappings = draw(st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.text(min_size=1, max_size=30),
            values=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10),
            min_size=0,
            max_size=5
        )
    ))
    
    respect_fk_order = draw(st.booleans())
    
    return TargetConfig(
        name=name,
        type=target_type,
        connection_string=connection_string,
        credentials=credentials,
        load_strategy=load_strategy,
        table_mappings=table_mappings,
        respect_fk_order=respect_fk_order
    )


@composite
def workflow_config_strategy(draw):
    """Generate a valid WorkflowConfig."""
    # Generate basic fields
    config_id = draw(st.uuids()).hex
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters=' -_.'
    )))
    description = draw(st.text(min_size=0, max_size=500))
    created_by = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='_-'
    )))
    
    # Generate datetime (limit to reasonable range to avoid serialization issues)
    created_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    
    # Generate path
    production_data_path = Path(draw(st.text(
        min_size=1, 
        max_size=100,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/_-.'
        )
    )))
    
    # Generation parameters
    sdv_model = draw(st.sampled_from(['gaussian_copula', 'ctgan', 'copula_gan']))
    bedrock_model = draw(st.sampled_from([
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-haiku-20240307-v1:0',
        'anthropic.claude-3-opus-20240229-v1:0'
    ]))
    num_synthetic_records = draw(st.integers(min_value=1, max_value=1000000))
    preserve_edge_cases = draw(st.booleans())
    edge_case_frequency = draw(st.floats(min_value=0.0, max_value=1.0))
    random_seed = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=2**31-1)))
    
    # Target systems
    targets = draw(st.lists(target_config_strategy(), min_size=0, max_size=5))
    
    # Test configuration
    test_framework = draw(st.sampled_from(['robot', 'selenium', 'playwright']))
    jira_test_tag = draw(st.text(min_size=0, max_size=50))
    parallel_execution = draw(st.booleans())
    
    # External integrations
    confluence_space = draw(st.text(min_size=0, max_size=50))
    jira_project = draw(st.text(min_size=0, max_size=50))
    
    # Flags
    demo_mode = draw(st.booleans())
    enable_cost_tracking = draw(st.booleans())
    
    # Tags
    tags = draw(st.lists(
        st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )),
        min_size=0,
        max_size=10
    ))
    
    return WorkflowConfig(
        id=config_id,
        name=name,
        description=description,
        created_by=created_by,
        created_at=created_at,
        production_data_path=production_data_path,
        sdv_model=sdv_model,
        bedrock_model=bedrock_model,
        num_synthetic_records=num_synthetic_records,
        preserve_edge_cases=preserve_edge_cases,
        edge_case_frequency=edge_case_frequency,
        random_seed=random_seed,
        targets=targets,
        test_framework=test_framework,
        jira_test_tag=jira_test_tag,
        parallel_execution=parallel_execution,
        confluence_space=confluence_space,
        jira_project=jira_project,
        demo_mode=demo_mode,
        enable_cost_tracking=enable_cost_tracking,
        tags=tags
    )


@settings(max_examples=100)
@given(config=workflow_config_strategy())
def test_config_roundtrip_dict(config):
    """
    Feature: synthetic-data-generator, Property 9: Configuration Round-Trip
    Validates: Requirements 30.4
    
    For any workflow configuration, converting to dict and back should preserve all settings.
    """
    # Convert to dict
    config_dict = config.to_dict()
    
    # Convert back to object
    restored_config = WorkflowConfig.from_dict(config_dict)
    
    # Verify all fields match
    assert restored_config.id == config.id
    assert restored_config.name == config.name
    assert restored_config.description == config.description
    assert restored_config.created_by == config.created_by
    assert restored_config.created_at == config.created_at
    assert restored_config.production_data_path == config.production_data_path
    assert restored_config.sdv_model == config.sdv_model
    assert restored_config.bedrock_model == config.bedrock_model
    assert restored_config.num_synthetic_records == config.num_synthetic_records
    assert restored_config.preserve_edge_cases == config.preserve_edge_cases
    assert restored_config.edge_case_frequency == config.edge_case_frequency
    assert restored_config.random_seed == config.random_seed
    assert restored_config.test_framework == config.test_framework
    assert restored_config.jira_test_tag == config.jira_test_tag
    assert restored_config.parallel_execution == config.parallel_execution
    assert restored_config.confluence_space == config.confluence_space
    assert restored_config.jira_project == config.jira_project
    assert restored_config.demo_mode == config.demo_mode
    assert restored_config.enable_cost_tracking == config.enable_cost_tracking
    assert restored_config.tags == config.tags
    
    # Verify targets
    assert len(restored_config.targets) == len(config.targets)
    for original_target, restored_target in zip(config.targets, restored_config.targets):
        assert restored_target.name == original_target.name
        assert restored_target.type == original_target.type
        assert restored_target.connection_string == original_target.connection_string
        assert restored_target.credentials == original_target.credentials
        assert restored_target.load_strategy == original_target.load_strategy
        assert restored_target.table_mappings == original_target.table_mappings
        assert restored_target.respect_fk_order == original_target.respect_fk_order


@settings(max_examples=100)
@given(config=workflow_config_strategy())
def test_config_roundtrip_json(config):
    """
    Feature: synthetic-data-generator, Property 9: Configuration Round-Trip
    Validates: Requirements 30.4
    
    For any workflow configuration, converting to JSON and back should preserve all settings.
    """
    # Convert to JSON string
    json_str = config.to_json()
    
    # Verify it's valid JSON
    json.loads(json_str)
    
    # Convert back to object
    restored_config = WorkflowConfig.from_json(json_str)
    
    # Verify all fields match
    assert restored_config.id == config.id
    assert restored_config.name == config.name
    assert restored_config.description == config.description
    assert restored_config.created_by == config.created_by
    assert restored_config.created_at == config.created_at
    assert restored_config.production_data_path == config.production_data_path
    assert restored_config.sdv_model == config.sdv_model
    assert restored_config.bedrock_model == config.bedrock_model
    assert restored_config.num_synthetic_records == config.num_synthetic_records
    assert restored_config.preserve_edge_cases == config.preserve_edge_cases
    assert restored_config.edge_case_frequency == config.edge_case_frequency
    assert restored_config.random_seed == config.random_seed
    assert restored_config.test_framework == config.test_framework
    assert restored_config.jira_test_tag == config.jira_test_tag
    assert restored_config.parallel_execution == config.parallel_execution
    assert restored_config.confluence_space == config.confluence_space
    assert restored_config.jira_project == config.jira_project
    assert restored_config.demo_mode == config.demo_mode
    assert restored_config.enable_cost_tracking == config.enable_cost_tracking
    assert restored_config.tags == config.tags
    
    # Verify targets
    assert len(restored_config.targets) == len(config.targets)
    for original_target, restored_target in zip(config.targets, restored_config.targets):
        assert restored_target.name == original_target.name
        assert restored_target.type == original_target.type
        assert restored_target.connection_string == original_target.connection_string
        assert restored_target.credentials == original_target.credentials
        assert restored_target.load_strategy == original_target.load_strategy
        assert restored_target.table_mappings == original_target.table_mappings
        assert restored_target.respect_fk_order == original_target.respect_fk_order


@settings(max_examples=100)
@given(config=workflow_config_strategy())
def test_config_double_roundtrip(config):
    """
    Feature: synthetic-data-generator, Property 9: Configuration Round-Trip
    Validates: Requirements 30.4
    
    For any workflow configuration, multiple round-trips should be idempotent.
    """
    # First round-trip
    json_str1 = config.to_json()
    restored1 = WorkflowConfig.from_json(json_str1)
    
    # Second round-trip
    json_str2 = restored1.to_json()
    restored2 = WorkflowConfig.from_json(json_str2)
    
    # Both JSON strings should be identical
    assert json_str1 == json_str2
    
    # All fields should match original
    assert restored2.id == config.id
    assert restored2.name == config.name
    assert restored2.created_at == config.created_at
    assert restored2.production_data_path == config.production_data_path
    assert restored2.num_synthetic_records == config.num_synthetic_records
    assert len(restored2.targets) == len(config.targets)
