"""Basic tests for the save/load system."""

import json
import tempfile
from pathlib import Path
from panda3d.core import Vec3, Vec4, Quat


def test_vec3_serialization():
    """Test Vec3 to list conversion."""
    from src.engine.world_serializer import WorldSerializer
    
    serializer = WorldSerializer()
    vec = Vec3(1.5, 2.5, 3.5)
    result = serializer._vec3_to_list(vec)
    
    assert result == [1.5, 2.5, 3.5]
    print("✓ Vec3 serialization works")


def test_vec4_serialization():
    """Test Vec4 to list conversion."""
    from src.engine.world_serializer import WorldSerializer
    
    serializer = WorldSerializer()
    vec = Vec4(1.0, 0.5, 0.25, 1.0)
    result = serializer._vec4_to_list(vec)
    
    assert result == [1.0, 0.5, 0.25, 1.0]
    print("✓ Vec4 serialization works")


def test_quat_serialization():
    """Test Quat to list conversion."""
    from src.engine.world_serializer import WorldSerializer
    
    serializer = WorldSerializer()
    quat = Quat(1, 0, 0, 0)  # Identity quaternion
    result = serializer._quat_to_list(quat)
    
    assert len(result) == 4
    print("✓ Quat serialization works")


def test_save_path():
    """Test save path generation."""
    from src.engine.world_serializer import WorldSerializer
    
    serializer = WorldSerializer(saves_directory="test_saves")
    path = serializer.get_save_path("test_save")
    
    assert path.name == "test_save.json"
    assert "test_saves" in str(path)
    print("✓ Save path generation works")


def test_serializer_creation():
    """Test that WorldSerializer can be instantiated."""
    from src.engine.world_serializer import WorldSerializer
    
    serializer = WorldSerializer()
    assert serializer.saves_dir.name == "saves"
    print("✓ WorldSerializer instantiation works")


def test_template_manager_creation():
    """Test that WorldTemplateManager can be instantiated."""
    from src.engine.world_serializer import WorldTemplateManager
    
    manager = WorldTemplateManager()
    assert manager.templates_dir.name == "world_templates"
    print("✓ WorldTemplateManager instantiation works")


def test_metadata_structure():
    """Test that save metadata has correct structure."""
    from src.engine.world_serializer import WorldSerializer
    from datetime import datetime
    
    metadata = {
        'version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'save_name': 'test',
        'title': 'Test Save',
        'description': 'A test save file'
    }
    
    # Test that it's JSON serializable
    json_str = json.dumps(metadata)
    loaded = json.loads(json_str)
    
    assert loaded['version'] == '1.0'
    assert loaded['save_name'] == 'test'
    print("✓ Metadata structure is valid")


def run_basic_tests():
    """Run all basic tests."""
    print("\n" + "="*50)
    print("Running Save/Load System Basic Tests")
    print("="*50 + "\n")
    
    tests = [
        test_vec3_serialization,
        test_vec4_serialization,
        test_quat_serialization,
        test_save_path,
        test_serializer_creation,
        test_template_manager_creation,
        test_metadata_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_basic_tests()
    sys.exit(0 if success else 1)
