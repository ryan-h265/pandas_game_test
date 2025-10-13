"""Visual brush indicator for terrain editing."""

from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    Geom,
    GeomLines,
    GeomNode,
)
import math


class BrushIndicator:
    """Visual indicator showing the terrain editing brush."""

    def __init__(self, render):
        """Initialize brush indicator.

        Args:
            render: Panda3D render node
        """
        self.render = render
        self.node_path = None
        self.visible = False
        self.size = 3.0
        self._create_indicator()

    def _create_indicator(self):
        """Create the visual indicator geometry."""
        # Create vertex data
        vformat = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData("brush", vformat, Geom.UHDynamic)

        # Create circle with line segments
        num_segments = 32
        vdata.setNumRows(num_segments + 1)

        vertex = GeomVertexWriter(vdata, "vertex")
        color = GeomVertexWriter(vdata, "color")

        # Create circle vertices
        for i in range(num_segments + 1):
            angle = (i / num_segments) * 2 * math.pi
            x = math.cos(angle) * self.size
            y = math.sin(angle) * self.size

            vertex.addData3(x, y, 0.1)  # Slightly above terrain
            color.addData4(1, 1, 0, 0.8)  # Yellow, semi-transparent

        # Create line loop
        lines = GeomLines(Geom.UHDynamic)
        for i in range(num_segments):
            lines.addVertices(i, i + 1)
        lines.addVertices(num_segments, 0)  # Close the loop
        lines.closePrimitive()

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(lines)

        # Create node
        node = GeomNode("brush_indicator")
        node.addGeom(geom)

        # Attach to render
        self.node_path = self.render.attachNewNode(node)
        self.node_path.setTransparency(True)
        self.node_path.setDepthTest(False)  # Always visible
        self.node_path.setDepthWrite(False)
        self.node_path.setBin("fixed", 0)
        self.node_path.hide()

    def update_position(self, position):
        """Update indicator position.

        Args:
            position: Vec3 world position
        """
        if self.node_path and position:
            self.node_path.setPos(position)

    def update_size(self, size):
        """Update indicator size.

        Args:
            size: Brush radius
        """
        if self.size != size:
            self.size = size
            # Recreate indicator with new size
            if self.node_path:
                self.node_path.removeNode()
            self._create_indicator()
            if self.visible:
                self.node_path.show()

    def show(self):
        """Show the indicator."""
        if self.node_path:
            self.node_path.show()
            self.visible = True

    def hide(self):
        """Hide the indicator."""
        if self.node_path:
            self.node_path.hide()
            self.visible = False

    def set_color(self, color):
        """Set indicator color based on mode.

        Args:
            color: Vec4 color (r, g, b, a)
        """
        # This would require recreating the geometry with new colors
        # For now, we'll just use the default yellow
        pass
