"""Color scheme definitions - Python port of colors.ts"""
from typing import Dict, List
from dataclasses import dataclass
import json


@dataclass
class Color:
    """A single color definition"""
    name: str
    hex: str


ColorScheme = Dict[str, str]


# Default (light) color list
DEFAULT_COLOR_LIST = [
    # Node colors
    Color("node.default", "#d3d3d3"),
    Color("node.entry", "#48AB30"),
    Color("node.exit", "#AB3030"),
    Color("node.throw", "#ffdddd"),
    Color("node.yield", "#00bfff"),
    Color("node.terminate", "#7256c6"),
    Color("node.border", "#000000"),
    Color("node.highlight", "#000000"),
    # Edge colors
    Color("edge.regular", "#0000ff"),
    Color("edge.consequence", "#008000"),
    Color("edge.alternative", "#ff0000"),
    # Cluster colors
    Color("cluster.border", "#ffffff"),
    Color("cluster.with", "#ffddff"),
    Color("cluster.tryComplex", "#ddddff"),
    Color("cluster.try", "#ddffdd"),
    Color("cluster.finally", "#ffffdd"),
    Color("cluster.except", "#ffdddd"),
    # Graph colors
    Color("graph.background", "#ffffff"),
]

# Dark color list
DARK_COLOR_LIST = [
    Color("node.default", "#707070"),
    Color("node.entry", "#48AB30"),
    Color("node.exit", "#AB3030"),
    Color("node.throw", "#590c0c"),
    Color("node.yield", "#0a9aca"),
    Color("node.terminate", "#7256c6"),
    Color("node.border", "#000000"),
    Color("node.highlight", "#dddddd"),
    Color("edge.regular", "#2592a1"),
    Color("edge.consequence", "#4ce34c"),
    Color("edge.alternative", "#ff3e3e"),
    Color("cluster.border", "#302e2e"),
    Color("cluster.with", "#7d007d"),
    Color("cluster.tryComplex", "#344c74"),
    Color("cluster.try", "#1b5f1b"),
    Color("cluster.finally", "#999918"),
    Color("cluster.except", "#590c0c"),
    Color("graph.background", "#1e1e1e"),
]


def list_to_scheme(colors: List[Color]) -> ColorScheme:
    """Convert a color list to a color scheme dictionary"""
    return {color.name: color.hex for color in colors}


def get_light_color_list() -> List[Color]:
    """Get the light color scheme"""
    return DEFAULT_COLOR_LIST.copy()


def get_dark_color_list() -> List[Color]:
    """Get the dark color scheme"""
    return DARK_COLOR_LIST.copy()


def get_default_color_list() -> List[Color]:
    """Get the default (light) color scheme"""
    return DEFAULT_COLOR_LIST.copy()


def get_default_color_scheme() -> ColorScheme:
    """Get the default color scheme as a dictionary"""
    return list_to_scheme(DEFAULT_COLOR_LIST)


def get_dark_color_scheme() -> ColorScheme:
    """Get the dark color scheme as a dictionary"""
    return list_to_scheme(DARK_COLOR_LIST)


def get_light_color_scheme() -> ColorScheme:
    """Get the light color scheme as a dictionary"""
    return list_to_scheme(DEFAULT_COLOR_LIST)


def serialize_color_list(color_list: List[Color]) -> str:
    """Serialize a color list to JSON"""
    data = {
        'version': 1,
        'scheme': [{'name': c.name, 'hex': c.hex} for c in color_list]
    }
    return json.dumps(data)


def deserialize_color_list(data: str) -> List[Color]:
    """Deserialize a color list from JSON"""
    parsed = json.loads(data)
    version = parsed.get('version')

    if version != 1:
        raise ValueError(f"Invalid scheme version: {version}")

    scheme = parsed.get('scheme', [])

    # Validate hex colors
    for item in scheme:
        hex_color = item.get('hex', '')
        if not hex_color.startswith('#') or not all(c in '0123456789abcdefABCDEF' for c in hex_color[1:]):
            raise ValueError(f"Invalid color: {hex_color}")

    return [Color(item['name'], item['hex']) for item in scheme]
