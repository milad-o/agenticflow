"""
Mermaid diagram generator for AgenticFlow visualizations.
Leverages mermaid-py package when available for enhanced functionality.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field

try:
    from mermaid import Mermaid
    MERMAID_PY_AVAILABLE = True
except ImportError:
    MERMAID_PY_AVAILABLE = False
    Mermaid = None


class DiagramType(Enum):
    """Supported Mermaid diagram types."""
    FLOWCHART = "flowchart"
    GRAPH = "graph"
    GITGRAPH = "gitgraph"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"


class FlowDirection(Enum):
    """Flowchart direction options."""
    TOP_DOWN = "TD"
    BOTTOM_UP = "BU"
    LEFT_RIGHT = "LR"
    RIGHT_LEFT = "RL"


class NodeShape(Enum):
    """Node shape options for flowcharts (supports both legacy and v11.3.0+ syntax)."""
    # Legacy syntax shapes
    RECTANGLE = "rect"
    ROUNDED = "round"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    PARALLELOGRAM = "parallelogram"
    TRAPEZOID = "trapezoid"
    CYLINDER = "cylinder"
    STADIUM = "stadium"
    
    # New v11.3.0+ shapes (using modern syntax)
    BANG = "bang"
    CARD = "card"
    CLOUD = "cloud"
    COLLATE = "collate"
    COM_LINK = "com-link"
    COMMENT = "comment"
    DATABASE = "database"
    DECISION = "decision"
    DELAY = "delay"
    DISPLAY = "display"
    DOCUMENT = "doc"
    EVENT = "event"
    EXTRACT = "extract"
    FORK = "fork"
    JUNCTION = "junction"
    MANUAL_FILE = "manual-file"
    MANUAL_INPUT = "manual-input"
    MANUAL_OPERATION = "manual"
    MULTI_DOCUMENT = "docs"
    MULTI_PROCESS = "processes"
    PAPER_TAPE = "paper-tape"
    PREPARE = "prepare"
    PRIORITY = "priority"
    PROCESS = "process"
    START = "start"
    STOP = "stop"
    STORED_DATA = "stored-data"
    SUBPROCESS = "subprocess"
    SUMMARY = "summary"
    TERMINAL = "terminal"
    TEXT_BLOCK = "text"


class EdgeType(Enum):
    """Edge/arrow types."""
    SOLID = "-->"
    DOTTED = "-.->"
    THICK = "==>"
    INVISIBLE = "~~~"


class MermaidTheme(Enum):
    """Predefined Mermaid themes."""
    DEFAULT = "default"
    NEUTRAL = "neutral"
    DARK = "dark"
    FOREST = "forest"
    BASE = "base"


@dataclass
class ThemeVariables:
    """Theme variables for customizing Mermaid appearance."""
    primary_color: Optional[str] = None
    primary_text_color: Optional[str] = None
    primary_border_color: Optional[str] = None
    line_color: Optional[str] = None
    secondary_color: Optional[str] = None
    tertiary_color: Optional[str] = None
    background: Optional[str] = None
    main_bkg: Optional[str] = None
    second_bkg: Optional[str] = None
    node_border: Optional[str] = None
    cluster_bkg: Optional[str] = None
    cluster_border: Optional[str] = None
    default_link_color: Optional[str] = None
    title_color: Optional[str] = None
    edge_label_background: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values."""
        result = {}
        field_mapping = {
            'primary_color': 'primaryColor',
            'primary_text_color': 'primaryTextColor',
            'primary_border_color': 'primaryBorderColor',
            'line_color': 'lineColor',
            'secondary_color': 'secondaryColor',
            'tertiary_color': 'tertiaryColor',
            'background': 'background',
            'main_bkg': 'mainBkg',
            'second_bkg': 'secondBkg',
            'node_border': 'nodeBorder',
            'cluster_bkg': 'clusterBkg',
            'cluster_border': 'clusterBorder',
            'default_link_color': 'defaultLinkColor',
            'title_color': 'titleColor',
            'edge_label_background': 'edgeLabelBackground',
        }
        
        for attr, value in self.__dict__.items():
            if value is not None:
                key = field_mapping.get(attr, attr)
                result[key] = value
        return result


@dataclass
class MermaidConfig:
    """Mermaid configuration for frontmatter."""
    theme: Optional[Union[MermaidTheme, str]] = None
    theme_variables: Optional[ThemeVariables] = None
    look: Optional[str] = None
    flow_chart: Optional[Dict[str, Any]] = None
    sequence: Optional[Dict[str, Any]] = None
    gantt: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {}
        
        if self.theme:
            if isinstance(self.theme, MermaidTheme):
                result['theme'] = self.theme.value
            else:
                result['theme'] = self.theme
        
        if self.theme_variables:
            theme_vars = self.theme_variables.to_dict()
            if theme_vars:
                result['themeVariables'] = theme_vars
        
        if self.look:
            result['look'] = self.look
        if self.flow_chart:
            result['flowchart'] = self.flow_chart
        if self.sequence:
            result['sequence'] = self.sequence
        if self.gantt:
            result['gantt'] = self.gantt
            
        return result


@dataclass
class Node:
    """Represents a node in the diagram."""
    id: str
    label: str
    shape: NodeShape = NodeShape.RECTANGLE
    css_class: Optional[str] = None
    style: Optional[Dict[str, str]] = None
    click_action: Optional[str] = None


@dataclass
class Edge:
    """Represents an edge/connection in the diagram."""
    from_node: str
    to_node: str
    label: Optional[str] = None
    edge_type: EdgeType = EdgeType.SOLID
    css_class: Optional[str] = None


@dataclass
class Subgraph:
    """Represents a subgraph/cluster."""
    id: str
    title: str
    nodes: List[str] = field(default_factory=list)
    direction: Optional[FlowDirection] = None


class MermaidGenerator:
    """
    Core Mermaid diagram generator for AgenticFlow visualizations.
    
    Supports various diagram types with customizable styling and layouts.
    Supports both legacy syntax and modern v11.3.0+ syntax.
    """
    
    def __init__(self, diagram_type: DiagramType = DiagramType.FLOWCHART, use_modern_syntax: bool = True):
        self.diagram_type = diagram_type
        self.direction = FlowDirection.TOP_DOWN
        self.use_modern_syntax = use_modern_syntax  # Use v11.3.0+ syntax by default
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.subgraphs: Dict[str, Subgraph] = {}
        self.styles: Dict[str, Dict[str, str]] = {}
        self.css_classes: Dict[str, Dict[str, str]] = {}
        
        # Frontmatter support
        self.title: Optional[str] = None
        self.config: Optional[MermaidConfig] = None
        self.display_sequence_numbers: Optional[bool] = None
        self.wrap_enabled: Optional[bool] = None
        
    def set_direction(self, direction: FlowDirection) -> "MermaidGenerator":
        """Set the diagram direction."""
        self.direction = direction
        return self
    
    def set_title(self, title: str) -> "MermaidGenerator":
        """Set the diagram title (appears in frontmatter)."""
        self.title = title
        return self
    
    def set_theme(self, theme: Union[MermaidTheme, str], theme_variables: Optional[ThemeVariables] = None) -> "MermaidGenerator":
        """Set the diagram theme and optional theme variables."""
        if self.config is None:
            self.config = MermaidConfig()
        self.config.theme = theme
        if theme_variables:
            self.config.theme_variables = theme_variables
        return self
    
    def set_config(self, config: MermaidConfig) -> "MermaidGenerator":
        """Set the complete Mermaid configuration."""
        self.config = config
        return self
    
    def add_theme_variable(self, key: str, value: str) -> "MermaidGenerator":
        """Add a single theme variable."""
        if self.config is None:
            self.config = MermaidConfig()
        if self.config.theme_variables is None:
            self.config.theme_variables = ThemeVariables()
        
        # Map common keys to ThemeVariables attributes
        attr_mapping = {
            'primaryColor': 'primary_color',
            'primaryTextColor': 'primary_text_color',
            'primaryBorderColor': 'primary_border_color',
            'lineColor': 'line_color',
            'secondaryColor': 'secondary_color',
            'tertiaryColor': 'tertiary_color',
            'background': 'background',
            'mainBkg': 'main_bkg',
            'secondBkg': 'second_bkg',
            'nodeBorder': 'node_border',
            'clusterBkg': 'cluster_bkg',
            'clusterBorder': 'cluster_border',
            'defaultLinkColor': 'default_link_color',
            'titleColor': 'title_color',
            'edgeLabelBackground': 'edge_label_background',
        }
        
        attr_name = attr_mapping.get(key, key)
        if hasattr(self.config.theme_variables, attr_name):
            setattr(self.config.theme_variables, attr_name, value)
        
        return self
        
    def add_node(
        self,
        node_id: str,
        label: str,
        shape: NodeShape = NodeShape.RECTANGLE,
        css_class: Optional[str] = None,
        style: Optional[Dict[str, str]] = None,
        click_action: Optional[str] = None
    ) -> "MermaidGenerator":
        """Add a node to the diagram."""
        self.nodes[node_id] = Node(
            id=node_id,
            label=label,
            shape=shape,
            css_class=css_class,
            style=style,
            click_action=click_action
        )
        return self
        
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        label: Optional[str] = None,
        edge_type: EdgeType = EdgeType.SOLID,
        css_class: Optional[str] = None
    ) -> "MermaidGenerator":
        """Add an edge between two nodes."""
        self.edges.append(Edge(
            from_node=from_node,
            to_node=to_node,
            label=label,
            edge_type=edge_type,
            css_class=css_class
        ))
        return self
        
    def add_subgraph(
        self,
        subgraph_id: str,
        title: str,
        nodes: Optional[List[str]] = None,
        direction: Optional[FlowDirection] = None
    ) -> "MermaidGenerator":
        """Add a subgraph/cluster."""
        self.subgraphs[subgraph_id] = Subgraph(
            id=subgraph_id,
            title=title,
            nodes=nodes or [],
            direction=direction
        )
        return self
        
    def add_style(self, node_id: str, styles: Dict[str, str]) -> "MermaidGenerator":
        """Add custom styles to a node."""
        self.styles[node_id] = styles
        return self
        
    def add_css_class(self, class_name: str, styles: Dict[str, str]) -> "MermaidGenerator":
        """Define a CSS class for styling."""
        self.css_classes[class_name] = styles
        return self
        
    def _format_node_shape(self, node: Node) -> str:
        """Format a node with its shape (supports both legacy and modern syntax)."""
        label = node.label.replace('"', '\\"')
        
        if self.use_modern_syntax:
            return self._format_modern_node_shape(node, label)
        else:
            return self._format_legacy_node_shape(node, label)
    
    def _format_modern_node_shape(self, node: Node, escaped_label: str) -> str:
        """Format node using modern v11.3.0+ syntax: A@{ shape: shape-name, label: "Label" }"""
        # Modern shapes that use the new @{ } syntax
        modern_shapes = {
            NodeShape.BANG, NodeShape.CARD, NodeShape.CLOUD, NodeShape.COLLATE,
            NodeShape.COM_LINK, NodeShape.COMMENT, NodeShape.DATABASE, NodeShape.DECISION,
            NodeShape.DELAY, NodeShape.DISPLAY, NodeShape.DOCUMENT, NodeShape.EVENT,
            NodeShape.EXTRACT, NodeShape.FORK, NodeShape.JUNCTION, NodeShape.MANUAL_FILE,
            NodeShape.MANUAL_INPUT, NodeShape.MANUAL_OPERATION, NodeShape.MULTI_DOCUMENT,
            NodeShape.MULTI_PROCESS, NodeShape.PAPER_TAPE, NodeShape.PREPARE, NodeShape.PRIORITY,
            NodeShape.PROCESS, NodeShape.START, NodeShape.STOP, NodeShape.STORED_DATA,
            NodeShape.SUBPROCESS, NodeShape.SUMMARY, NodeShape.TERMINAL, NodeShape.TEXT_BLOCK
        }
        
        if node.shape in modern_shapes:
            return f'{node.id}@{{ shape: {node.shape.value}, label: "{escaped_label}" }}'
        else:
            # Fall back to legacy syntax for basic shapes
            return self._format_legacy_node_shape(node, escaped_label)
    
    def _format_legacy_node_shape(self, node: Node, escaped_label: str) -> str:
        """Format node using legacy syntax for basic shapes."""
        legacy_formats = {
            NodeShape.RECTANGLE: f'{node.id}["{escaped_label}"]',
            NodeShape.ROUNDED: f'{node.id}("{escaped_label}")',
            NodeShape.CIRCLE: f'{node.id}(("{escaped_label}"))',
            NodeShape.DIAMOND: f'{node.id}{{"{escaped_label}"}}',
            NodeShape.HEXAGON: f'{node.id}{{{{"{escaped_label}"}}}}',
            NodeShape.PARALLELOGRAM: f'{node.id}[/"{escaped_label}"/]',
            NodeShape.TRAPEZOID: f'{node.id}[\\"{escaped_label}"\\]',
            NodeShape.CYLINDER: f'{node.id}[("{escaped_label}")]',
            NodeShape.STADIUM: f'{node.id}(["{escaped_label}"])',
            # For modern shapes when using legacy mode, use rectangle as fallback
            NodeShape.PROCESS: f'{node.id}["{escaped_label}"]',
            NodeShape.DATABASE: f'{node.id}[("{escaped_label}")]',
            NodeShape.DECISION: f'{node.id}{{"{escaped_label}"}}',
            NodeShape.START: f'{node.id}(("{escaped_label}"))',
            NodeShape.TERMINAL: f'{node.id}(["{escaped_label}"])',
        }
        
        return legacy_formats.get(node.shape, f'{node.id}["{escaped_label}"]')
    
    def _generate_frontmatter(self) -> List[str]:
        """Generate YAML frontmatter for the diagram."""
        frontmatter_lines = ["---"]
        
        if self.title:
            frontmatter_lines.append(f"title: {self.title}")
        
        if self.config:
            config_dict = self.config.to_dict()
            if config_dict:
                frontmatter_lines.append("config:")
                frontmatter_lines.extend(self._dict_to_yaml(config_dict, indent=2))
        
        if self.display_sequence_numbers is not None:
            frontmatter_lines.append(f"displaySequenceNumbers: {str(self.display_sequence_numbers).lower()}")
        
        if self.wrap_enabled is not None:
            frontmatter_lines.append(f"wrap: {str(self.wrap_enabled).lower()}")
        
        frontmatter_lines.append("---")
        return frontmatter_lines
    
    def _dict_to_yaml(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """Convert dictionary to YAML-like format."""
        lines = []
        spaces = " " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{spaces}{key}:")
                lines.extend(self._dict_to_yaml(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{spaces}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{spaces}  -")
                        lines.extend(self._dict_to_yaml(item, indent + 4))
                    else:
                        lines.append(f"{spaces}  - {item}")
            elif isinstance(value, str):
                # Handle strings that might need quoting
                if ' ' in value or ':' in value or value.startswith('#'):
                    lines.append(f'{spaces}{key}: "{value}"')
                else:
                    lines.append(f"{spaces}{key}: {value}")
            else:
                lines.append(f"{spaces}{key}: {value}")
        
        return lines
        
    def _format_edge(self, edge: Edge) -> str:
        """Format an edge with optional label."""
        if edge.label:
            label = edge.label.replace('"', '\\"')
            return f'{edge.from_node} {edge.edge_type.value}|"{label}"| {edge.to_node}'
        else:
            return f'{edge.from_node} {edge.edge_type.value} {edge.to_node}'
            
    def generate(self) -> str:
        """Generate the complete Mermaid diagram with optional frontmatter."""
        lines = []
        
        # Add frontmatter if configured
        if self.title or self.config:
            lines.extend(self._generate_frontmatter())
            lines.append("")
        
        # Diagram header
        if self.diagram_type == DiagramType.FLOWCHART:
            lines.append(f"flowchart {self.direction.value}")
        else:
            lines.append(self.diagram_type.value)
            
        lines.append("")
        
        # Subgraphs
        for subgraph in self.subgraphs.values():
            escaped_title = subgraph.title.replace('"', '\\"')
            lines.append(f"    subgraph {subgraph.id} [\"{escaped_title}\"]")
            if subgraph.direction:
                lines.append(f"        direction {subgraph.direction.value}")
            for node_id in subgraph.nodes:
                if node_id in self.nodes:
                    lines.append(f"        {self._format_node_shape(self.nodes[node_id])}")
            lines.append("    end")
            lines.append("")
            
        # Standalone nodes (not in subgraphs)
        subgraph_nodes = {node for sg in self.subgraphs.values() for node in sg.nodes}
        for node in self.nodes.values():
            if node.id not in subgraph_nodes:
                lines.append(f"    {self._format_node_shape(node)}")
                
        if any(node.id not in subgraph_nodes for node in self.nodes.values()):
            lines.append("")
            
        # Edges
        for edge in self.edges:
            lines.append(f"    {self._format_edge(edge)}")
            
        if self.edges:
            lines.append("")
            
        # Node styles
        for node_id, styles in self.styles.items():
            style_str = ",".join(f"{k}:{v}" for k, v in styles.items())
            lines.append(f"    style {node_id} {style_str}")
            
        # CSS classes
        for class_name, styles in self.css_classes.items():
            style_str = ",".join(f"{k}:{v}" for k, v in styles.items())
            lines.append(f"    classDef {class_name} {style_str}")
            
        # Apply CSS classes to nodes
        for node in self.nodes.values():
            if node.css_class:
                lines.append(f"    class {node.id} {node.css_class}")
                
        # Click actions
        for node in self.nodes.values():
            if node.click_action:
                lines.append(f"    click {node.id} {node.click_action}")
                
        return "\n".join(lines)
        
    def clear(self) -> "MermaidGenerator":
        """Clear all diagram data."""
        self.nodes.clear()
        self.edges.clear()
        self.subgraphs.clear()
        self.styles.clear()
        self.css_classes.clear()
        return self
        
    def clone(self) -> "MermaidGenerator":
        """Create a copy of the generator."""
        new_gen = MermaidGenerator(self.diagram_type)
        new_gen.direction = self.direction
        new_gen.nodes = self.nodes.copy()
        new_gen.edges = self.edges.copy()
        new_gen.subgraphs = self.subgraphs.copy()
        new_gen.styles = self.styles.copy()
        new_gen.css_classes = self.css_classes.copy()
        return new_gen
        
    def render_to_svg(self) -> Optional[str]:
        """Render the diagram to SVG using mermaid-py if available."""
        if not MERMAID_PY_AVAILABLE:
            return None
            
        try:
            # mermaid-py expects the diagram code in the constructor
            from mermaid import Mermaid
            diagram_code = self.generate()
            mermaid_instance = Mermaid(diagram_code)
            return mermaid_instance.svg_response.text
        except Exception as e:
            print(f"mermaid-py rendering failed: {e}")
            return None
            
    def export_svg(self, output_path: str) -> bool:
        """Export diagram to SVG file."""
        svg_content = self.render_to_svg()
        if svg_content:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                return True
            except Exception as e:
                print(f"SVG export failed: {e}")
                return False
        return False
        
    def has_mermaid_py(self) -> bool:
        """Check if mermaid-py package is available."""
        return MERMAID_PY_AVAILABLE
        
    def draw(self, output_path: Optional[str] = None, format: str = "png", 
            width: int = 1200, height: int = 800) -> bool:
        """Draw the diagram and save/display it (LangGraph-style interface).
        
        Args:
            output_path: Path to save the image. If None, uses temporary file
            format: Output format (png, svg, pdf)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if successful, False otherwise
        """
        if not output_path:
            import tempfile
            output_path = tempfile.mktemp(suffix=f".{format}")
            
        diagram_code = self.generate()
        
        # Try different export backends
        from .export_utils import get_exporter
        exporter = get_exporter()
        
        if format.lower() == "svg":
            success = exporter.export_to_svg(diagram_code, output_path)
        elif format.lower() == "png":
            success = exporter.export_to_png(diagram_code, output_path, width=width, height=height)
        elif format.lower() == "pdf":
            success = exporter.export_to_pdf(diagram_code, output_path)
        else:
            print(f"Unsupported format: {format}")
            return False
            
        if success:
            print(f"Diagram saved to: {output_path}")
            # Try to open the file on macOS
            if output_path.startswith("/tmp"):
                try:
                    import subprocess
                    subprocess.run(["open", output_path], check=False)
                except Exception:
                    pass
        
        return success
        
    def show(self, format: str = "png", width: int = 1200, height: int = 800) -> bool:
        """Show the diagram in a viewer.
        
        Args:
            format: Output format (png, svg, pdf)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if successful, False otherwise
        """
        import tempfile
        temp_path = tempfile.mktemp(suffix=f".{format}")
        return self.draw(temp_path, format, width, height)
        
    def _repr_html_(self) -> str:
        """Return HTML representation for Jupyter notebooks."""
        try:
            # Try to render as SVG for inline display
            svg_content = self.render_to_svg()
            if svg_content:
                # Wrap SVG in a div with some basic styling
                return f"""
                <div style="text-align: center; margin: 10px;">
                    {svg_content}
                </div>
                """
            else:
                # Fallback to showing the Mermaid code
                diagram_code = self.generate()
                return f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px;">
                    <h4>Mermaid Diagram</h4>
                    <pre style="background-color: #e9ecef; padding: 10px; border-radius: 3px;">{diagram_code}</pre>
                    <p><em>Install additional dependencies for inline rendering: <code>pip install mermaid-py</code></em></p>
                </div>
                """
        except Exception as e:
            return f"""
            <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 10px; color: #c62828;">
                <h4>Visualization Error</h4>
                <p>Failed to render diagram: {str(e)}</p>
            </div>
            """


# Predefined color schemes and styles
class ColorSchemes:
    """Predefined color schemes for different visualization types."""
    
    AGENT_COLORS = {
        "supervisor": {"fill": "#ff6b6b", "stroke": "#c92a2a", "color": "#fff"},
        "worker": {"fill": "#4ecdc4", "stroke": "#20b2aa", "color": "#fff"},
        "specialist": {"fill": "#45b7d1", "stroke": "#1890ff", "color": "#fff"},
        "coordinator": {"fill": "#96ceb4", "stroke": "#52b788", "color": "#fff"},
    }
    
    TOOL_COLORS = {
        "default": {"fill": "#ffd93d", "stroke": "#f59e0b", "color": "#000"},
        "llm": {"fill": "#a78bfa", "stroke": "#7c3aed", "color": "#fff"},
        "external": {"fill": "#fb7185", "stroke": "#e11d48", "color": "#fff"},
        "database": {"fill": "#34d399", "stroke": "#10b981", "color": "#000"},
    }
    
    TASK_COLORS = {
        "pending": {"fill": "#e5e7eb", "stroke": "#9ca3af", "color": "#000"},
        "running": {"fill": "#fbbf24", "stroke": "#f59e0b", "color": "#000"},
        "completed": {"fill": "#34d399", "stroke": "#10b981", "color": "#000"},
        "failed": {"fill": "#f87171", "stroke": "#ef4444", "color": "#fff"},
    }


def create_agent_visualization_styles() -> Dict[str, Dict[str, str]]:
    """Create predefined CSS classes for agent visualization."""
    styles = {}
    
    for agent_type, colors in ColorSchemes.AGENT_COLORS.items():
        styles[f"agent-{agent_type}"] = colors
        
    for tool_type, colors in ColorSchemes.TOOL_COLORS.items():
        styles[f"tool-{tool_type}"] = colors
        
    for task_state, colors in ColorSchemes.TASK_COLORS.items():
        styles[f"task-{task_state}"] = colors
        
    return styles