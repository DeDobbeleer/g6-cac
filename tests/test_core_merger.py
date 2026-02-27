"""Tests for core merger functionality."""

import pytest
from cac_configmgr.core.merger import (
    merge_resources,
    deep_merge,
    merge_list_by_id,
    apply_ordering_directives,
)


class TestMergeResources:
    """Test resource merging by name."""
    
    def test_merge_same_resource(self):
        """Test merging two resources with same name."""
        base = [{"name": "repo-secu", "retention": 365}]
        override = [{"name": "repo-secu", "retention": 90}]
        
        result = merge_resources(base, override)
        
        assert len(result) == 1
        assert result[0]["retention"] == 90
    
    def test_append_new_resource(self):
        """Test appending new resource with different name."""
        base = [{"name": "repo-secu", "retention": 365}]
        override = [{"name": "repo-new", "retention": 180}]
        
        result = merge_resources(base, override)
        
        assert len(result) == 2
        assert result[0]["name"] == "repo-secu"
        assert result[1]["name"] == "repo-new"
    
    def test_delete_resource(self):
        """Test deleting resource with _action: delete."""
        base = [
            {"name": "repo-secu", "retention": 365},
            {"name": "repo-old", "retention": 30}
        ]
        override = [{"name": "repo-old", "_action": "delete"}]
        
        result = merge_resources(base, override)
        
        assert len(result) == 1
        assert result[0]["name"] == "repo-secu"


class TestDeepMerge:
    """Test deep merging of dictionaries."""
    
    def test_simple_override(self):
        """Test simple field override."""
        base = {"name": "repo-secu", "retention": 365}
        override = {"retention": 90}
        
        result = deep_merge(base, override)
        
        assert result["name"] == "repo-secu"
        assert result["retention"] == 90
    
    def test_merge_list_by_id(self):
        """Test merging lists with _id matching."""
        base = {
            "name": "repo-secu",
            "hiddenrepopath": [
                {"_id": "fast-tier", "path": "/opt/immune/storage", "retention": 30}
            ]
        }
        override = {
            "hiddenrepopath": [
                {"_id": "fast-tier", "retention": 7}  # Override only retention
            ]
        }
        
        result = deep_merge(base, override)
        
        assert len(result["hiddenrepopath"]) == 1
        tier = result["hiddenrepopath"][0]
        assert tier["_id"] == "fast-tier"
        assert tier["path"] == "/opt/immune/storage"  # Inherited
        assert tier["retention"] == 7  # Overridden


class TestMergeListById:
    """Test list merging with _id matching and ordering."""
    
    def test_merge_existing_element(self):
        """Test merging element with same _id."""
        base = [
            {"_id": "tier1", "path": "/storage", "retention": 30}
        ]
        override = [
            {"_id": "tier1", "retention": 7}  # Partial override
        ]
        
        result = merge_list_by_id(base, override)
        
        assert len(result) == 1
        assert result[0]["path"] == "/storage"
        assert result[0]["retention"] == 7
    
    def test_append_new_element(self):
        """Test appending new element with new _id."""
        base = [
            {"_id": "tier1", "path": "/storage", "retention": 30}
        ]
        override = [
            {"_id": "tier2", "path": "/storage-warm", "retention": 90}
        ]
        
        result = merge_list_by_id(base, override)
        
        assert len(result) == 2
    
    def test_delete_element(self):
        """Test deleting element with _action: delete."""
        base = [
            {"_id": "tier1", "path": "/storage"},
            {"_id": "tier2", "path": "/storage-warm"}
        ]
        override = [
            {"_id": "tier1", "_action": "delete"}
        ]
        
        result = merge_list_by_id(base, override)
        
        assert len(result) == 1
        assert result[0]["_id"] == "tier2"
    
    def test_ordering_after(self):
        """Test _after ordering directive."""
        base = [
            {"_id": "first", "value": 1},
            {"_id": "second", "value": 2}
        ]
        override = [
            {"_id": "middle", "value": 1.5, "_after": "first"}
        ]
        
        result = merge_list_by_id(base, override)
        
        ids = [r["_id"] for r in result]
        assert ids == ["first", "middle", "second"]
    
    def test_ordering_position(self):
        """Test _position ordering directive."""
        base = [
            {"_id": "a", "value": 1},
            {"_id": "b", "value": 2},
            {"_id": "c", "value": 3}
        ]
        override = [
            {"_id": "b", "_position": 1}  # Move to first position
        ]
        
        result = merge_list_by_id(base, override)
        
        ids = [r["_id"] for r in result]
        assert ids[0] == "b"


class TestApplyOrderingDirectives:
    """Test ordering directive application."""
    
    def test_position_priority(self):
        """Test that _position takes priority over _first/_last."""
        items = ["a", "b", "c"]
        directives = [
            ("b", "_first", True),
            ("b", "_position", 3)  # Should win
        ]
        
        result = apply_ordering_directives(items, directives)
        
        assert result[2] == "b"  # Position 3 (index 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
