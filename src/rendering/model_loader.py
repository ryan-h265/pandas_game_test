"""Model loader utility for loading glTF and other 3D formats."""

from panda3d.core import NodePath
import os


class ModelLoader:
    """Utility class for loading 3D models with error handling."""

    def __init__(self, base_loader=None):
        """Initialize the model loader.

        Args:
            base_loader: ShowBase.loader instance (optional, will get from builtins if not provided)
        """
        if base_loader is None:
            # Try to get the global loader from builtins (set by ShowBase)
            try:
                import builtins
                if hasattr(builtins, 'loader'):
                    self.loader = builtins.loader
                else:
                    print("WARNING: No global loader found. ModelLoader may not work correctly.")
                    self.loader = None
            except:
                self.loader = None
        else:
            self.loader = base_loader

        self._model_cache = {}

    def load_gltf(self, path, cache=True):
        """Load a glTF or GLB model.

        Args:
            path: Path to the .gltf or .glb file (relative to project root or absolute)
            cache: Whether to cache the loaded model for reuse

        Returns:
            NodePath containing the loaded model, or None if loading failed
        """
        if not self.loader:
            print("ERROR: No loader available")
            return None

        # Check cache first
        if cache and path in self._model_cache:
            print(f"Loading model from cache: {path}")
            return self._model_cache[path].copyTo(NodePath())

        # Convert to absolute path if relative
        if not os.path.isabs(path):
            # Get the project root directory (where main.py is run from)
            abs_path = os.path.abspath(path)
        else:
            abs_path = path

        # Check if file exists
        if not os.path.exists(abs_path):
            print(f"ERROR: Model file not found: {abs_path}")
            return None

        try:
            # Load the glTF model using panda3d-gltf
            # Panda3D's loader will automatically use the panda3d-gltf plugin
            print(f"Loading glTF model: {abs_path}")

            # Use Panda3D's Filename class for proper path handling
            from panda3d.core import Filename
            panda_path = Filename.fromOsSpecific(abs_path)

            model = self.loader.loadModel(panda_path)

            if model is None or model.isEmpty():
                print(f"ERROR: Failed to load model: {abs_path}")
                return None

            print(f"Successfully loaded model: {abs_path}")

            # Cache the model if requested
            if cache:
                self._model_cache[path] = model

            # Return a copy so the original cache stays intact
            return model if not cache else model.copyTo(NodePath())

        except Exception as e:
            print(f"ERROR: Exception while loading model {abs_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_model(self, path, cache=True):
        """Load any supported model format (.gltf, .glb, .bam, .egg).

        Args:
            path: Path to the model file
            cache: Whether to cache the loaded model

        Returns:
            NodePath containing the loaded model, or None if loading failed
        """
        extension = os.path.splitext(path)[1].lower()

        # For glTF/GLB, use the dedicated loader
        if extension in ['.gltf', '.glb']:
            return self.load_gltf(path, cache)

        # For other formats, use standard Panda3D loader
        try:
            # Check cache
            if cache and path in self._model_cache:
                print(f"Loading model from cache: {path}")
                return self._model_cache[path].copyTo(NodePath())

            print(f"Loading model: {path}")
            model = self.loader.loadModel(path)

            if model is None or model.isEmpty():
                print(f"ERROR: Failed to load model: {path}")
                return None

            print(f"Successfully loaded model: {path}")

            # Cache if requested
            if cache:
                self._model_cache[path] = model

            return model if not cache else model.copyTo(NodePath())

        except Exception as e:
            print(f"ERROR: Exception while loading model {path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def clear_cache(self):
        """Clear the model cache to free memory."""
        self._model_cache.clear()
        print("Model cache cleared")


# Global model loader instance
_global_model_loader = None


def get_model_loader():
    """Get the global model loader instance.

    Returns:
        ModelLoader: Global model loader instance
    """
    global _global_model_loader
    if _global_model_loader is None:
        _global_model_loader = ModelLoader()
    return _global_model_loader
