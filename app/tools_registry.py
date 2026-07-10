"""Registry of all tools in the toolkit.

To add a new tool:
    1. Create a QWidget subclass (e.g. in app/tabs/my_tool_tab.py)
    2. Import it below
    3. Add an entry to TOOLS
"""

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from app.tabs.compress_tab import CompressTab
from app.tabs.resize_tab import ResizeTab
from app.tabs.convert_tab import ConvertTab
from app.tabs.rotate_tab import RotateTab
from app.tabs.watermark_tab import WatermarkTab


@dataclass
class Tool:
    key: str
    name: str
    subtitle: str
    factory: Callable[[], QWidget]
    icon: str = ""


TOOLS: list[Tool] = [
    Tool(
        key="compress",
        name="Compress",
        subtitle="Reduce file size with quality control",
        factory=CompressTab,
        icon="🗜️",
    ),
    Tool(
        key="resize",
        name="Resize",
        subtitle="Resize images by dimensions or percentage",
        factory=ResizeTab,
        icon="📐",
    ),
    Tool(
        key="convert",
        name="Convert",
        subtitle="Convert images to JPG, PNG, or WebP",
        factory=ConvertTab,
        icon="🔄",
    ),
    Tool(
        key="rotate",
        name="Rotate & Flip",
        subtitle="Rotate or flip images in bulk",
        factory=RotateTab,
        icon="🔁",
    ),
    Tool(
        key="watermark",
        name="Watermark",
        subtitle="Add text or image watermarks with live preview",
        factory=WatermarkTab,
        icon="🖼️",
    ),
]
