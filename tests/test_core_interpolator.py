"""Tests for core interpolator functionality."""

import pytest
from cac_configmgr.core.interpolator import (
    Interpolator,
    VariableNotFoundError,
    merge_variables,
)


class TestInterpolator:
    """Test variable interpolation."""
    
    def test_interpolate_string_variable(self):
        """Test interpolating a single variable."""
        interp = Interpolator({"retention": 90})
        result = interp.interpolate("{{retention}}")
        
        assert result == 90  # Preserves type
    
    def test_interpolate_in_string(self):
        """Test interpolating within a string."""
        interp = Interpolator({"path": "/opt/immune/storage"})
        result = interp.interpolate("Mount point: {{path}}")
        
        assert result == "Mount point: /opt/immune/storage"
    
    def test_interpolate_dict(self):
        """Test interpolating in dictionary values."""
        interp = Interpolator({"retention": 365, "path": "/storage"})
        result = interp.interpolate({
            "name": "repo-secu",
            "retention": "{{retention}}",
            "path": "{{path}}"
        })
        
        assert result["retention"] == 365
        assert result["path"] == "/storage"
        assert result["name"] == "repo-secu"  # Unchanged
    
    def test_interpolate_list(self):
        """Test interpolating in list items."""
        interp = Interpolator({"tier1_retention": 7, "tier2_retention": 90})
        result = interp.interpolate([
            {"_id": "tier1", "retention": "{{tier1_retention}}"},
            {"_id": "tier2", "retention": "{{tier2_retention}}"}
        ])
        
        assert result[0]["retention"] == 7
        assert result[1]["retention"] == 90
    
    def test_variable_not_found(self):
        """Test error when variable not defined."""
        interp = Interpolator({})
        
        with pytest.raises(VariableNotFoundError) as exc_info:
            interp.interpolate("{{undefined_var}}")
        
        assert "undefined_var" in str(exc_info.value)
    
    def test_preserve_internal_fields(self):
        """Test that _id and internal fields are not interpolated."""
        interp = Interpolator({"id": "should_not_be_used"})
        result = interp.interpolate({
            "_id": "fast-tier",
            "name": "{{id}}"  # This should interpolate
        })
        
        assert result["_id"] == "fast-tier"  # Unchanged
        assert result["name"] == "should_not_be_used"
    
    def test_preserve_bool_type(self):
        """Test that boolean values preserve their type."""
        interp = Interpolator({"enabled": True})
        result = interp.interpolate("{{enabled}}")
        
        assert result is True
        assert isinstance(result, bool)
    
    def test_preserve_int_type(self):
        """Test that integer values preserve their type."""
        interp = Interpolator({"count": 42})
        result = interp.interpolate("{{count}}")
        
        assert result == 42
        assert isinstance(result, int)


class TestMergeVariables:
    """Test variable merging."""
    
    def test_merge_override_wins(self):
        """Test that override variables take precedence."""
        base = {"retention": 365, "path": "/storage"}
        override = {"retention": 90}
        
        result = merge_variables(base, override)
        
        assert result["retention"] == 90  # Overridden
        assert result["path"] == "/storage"  # Preserved
    
    def test_merge_adds_new(self):
        """Test that new variables are added."""
        base = {"retention": 365}
        override = {"path": "/storage"}
        
        result = merge_variables(base, override)
        
        assert result["retention"] == 365
        assert result["path"] == "/storage"


class TestExtractVariables:
    """Test variable extraction from objects."""
    
    def test_extract_from_string(self):
        """Test extracting variable names from string."""
        result = Interpolator.extract_variables("{{var1}} and {{var2}}")
        
        assert result == {"var1", "var2"}
    
    def test_extract_from_dict(self):
        """Test extracting from nested dict."""
        result = Interpolator.extract_variables({
            "field1": "{{var1}}",
            "field2": {
                "nested": "{{var2}}"
            }
        })
        
        assert result == {"var1", "var2"}
    
    def test_extract_from_list(self):
        """Test extracting from list."""
        result = Interpolator.extract_variables([
            "{{var1}}",
            {"field": "{{var2}}"}
        ])
        
        assert result == {"var1", "var2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
