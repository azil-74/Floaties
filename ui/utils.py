# ui/utils.py

def load_colored_svg(filename: str, color_hex: str):
    """Reads an SVG, injects the theme color, and returns a QIcon."""
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtGui import QPixmap, QIcon
    from pathlib import Path
    
    filepath = Path(__file__).parent.parent / "assets" / filename
    if not filepath.exists():
        return QIcon()
        
    with open(filepath, 'r', encoding='utf-8') as f:
        svg_data = f.read()

    svg_data = svg_data.replace("#TEXT_COLOR#", color_hex)
    
    arr = QByteArray(svg_data.encode('utf-8'))
    pix = QPixmap()
    pix.loadFromData(arr, "SVG")
    return QIcon(pix)