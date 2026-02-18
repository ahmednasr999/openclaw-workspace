---
name: diagram-generator
description: Generate professional diagrams (Excalidraw, Draw.io, Mermaid) from JSON specifications. Create architecture diagrams, flowcharts, mind maps, and more with hand-drawn aesthetic.
---

# Diagram Generator MCP

Generate diagrams from structured JSON specifications. Supports Excalidraw, Draw.io, and Mermaid formats.

## Quick Start

```bash
# Generate Excalidraw diagram
mcporter call diagram.generate_diagram diagram_spec="{
  \"title\": \"My Diagram\",
  \"format\": \"excalidraw\",
  \"elements\": [...]
}"

# Export to PNG
excalidraw-export diagram.excalidraw --output diagram.png
```

## Element Types

### Container (Layer/Group)
```json
{
  "id": "layer1",
  "type": "container",
  "name": "Layer Name",
  "geometry": {"x": 50, "y": 50, "width": 400, "height": 200},
  "style": {"fillColor": "#e8f4fd", "strokeColor": "#3498db", "strokeWidth": 2},
  "children": [...]
}
```

### Node (Basic Element)
```json
{
  "id": "node1",
  "type": "node",
  "name": "Component Name",
  "shape": "rect" | "ellipse" | "diamond" | "rounded" | "cylinder" | "cloud",
  "geometry": {"x": 100, "y": 100, "width": 120, "height": 60},
  "style": {"fillColor": "#fff", "strokeColor": "#333", "strokeWidth": 1}
}
```

### Edge (Connection)
```json
{
  "id": "edge1",
  "type": "edge",
  "source": "node1",
  "target": "node2",
  "label": "Connection Label",
  "style": {"strokeColor": "#666", "strokeWidth": 2}
}
```

## Diagram Types

| Type | Format | Best For |
|------|--------|----------|
| Architecture | Excalidraw/Draw.io | System diagrams, layered architecture |
| Flowchart | Mermaid/Draw.io | Business processes, algorithms |
| Sequence | Mermaid | API calls, message flows |
| Mind Map | Mermaid/Excalidraw | Hierarchical ideas |
| ER Diagram | Mermaid/Draw.io | Database schemas |

## Style Colors (by Layer)

| Layer | Fill Color | Border Color |
|-------|------------|--------------|
| Client | #e3f2fd | #1976d2 |
| Gateway | #f3e5f5 | #7b1fa2 |
| Service | #e8f5e9 | #388e3c |
| Data | #fff3e0 | #f57c00 |
| External | #fce4ec | #c2185b |

## Output Locations

- **Excalidraw:** `/root/.openclaw/workspace/config/diagrams/excalidraw/`
- **Draw.io:** `/root/.openclaw/workspace/config/diagrams/drawio/`
- **Mermaid:** `/root/.openclaw/workspace/config/diagrams/mermaid/`

## Example: OpenClaw Architecture

```json
{
  "title": "OpenClaw Architecture",
  "format": "excalidraw",
  "elements": [
    {
      "id": "channels",
      "type": "container",
      "name": "📡 Channels",
      "geometry": {"x": 50, "y": 50, "width": 400, "height": 100},
      "style": {"fillColor": "#e8f4fd", "strokeColor": "#3498db"},
      "children": [
        {"id": "tg", "type": "node", "name": "✉️ Telegram", "shape": "rect", ...},
        {"id": "wa", "type": "node", "name": "💬 WhatsApp", "shape": "rect", ...}
      ]
    }
  ]
}
```

## Export Commands

```bash
# PNG (default)
excalidraw-export diagram.excalidraw

# PNG with scale
excalidraw-export diagram.excalidraw --scale 3

# SVG
excalidraw-export diagram.excalidraw --svg

# Custom output path
excalidraw-export input.excalidraw -o /path/to/output.png
```

## Common Tasks

### Architecture Diagram
Use Excalidraw format with containers for layers, nodes for components.

### Flowchart
Use Mermaid for automatic layout or Excalidraw for manual positioning.

### Mind Map
Use Mermaid mindmap syntax or Excalidraw with hierarchical containers.

## Tips

- Use containers for layers to group related components
- Add edges with labels to show data flow
- Use consistent colors per layer type
- Excalidraw has authentic hand-drawn style
- Export to PNG for LinkedIn/social media
