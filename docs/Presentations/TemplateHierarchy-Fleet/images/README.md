# Diagram Images

This folder contains exported PNG images from the draw.io schema files.

## Expected Files

### From 01-fleet-architecture.drawio

| Filename | Source Page | Description |
|----------|-------------|-------------|
| `01-node-roles.png` | Page 1: "1. Node Roles" | DataNode, SearchHead, AIO capabilities and fleet tags |
| `02-simple-arch.png` | Page 2: "2. Simple Achitecture" | Single AIO or simple distributed mode |
| `03-medium-dist.png` | Page 3: "3. Medium Distributed" | 2 backend clusters + 1 Search Head |
| `04-complex-ent.png` | Page 4: "4. Complex Enterprise" | Production cluster + DR + SH cluster |

### From 02-template-hierarchy.drawio

| Filename | Source Page | Description |
|----------|-------------|-------------|
| `05-4level-overview.png` | Page 1: "Overview 4 Levels" | Hierarchical template system (4 levels) |
| `06-merge-mechanisms.png` | Page 2: "Merge Mechanisms" | Deep merge and list merging with _id |
| `07-complete-example.png` | Page 3: "Complete Repo Example" | Full repo inheritance chain example |

## Export Settings

- **Format**: PNG
- **Border**: 10px
- **Crop**: Crop to Content
- **DPI**: 300 (for crisp display)

## How to Export

### Option A: draw.io Desktop App
1. Open `.drawio` file
2. Select page
3. File → Export as → PNG
4. Set border to 10, enable "Crop to Content"
5. Save with filename from table above

### Option B: draw.io Web (app.diagrams.net)
1. Go to https://app.diagrams.net
2. File → Open from → Device → Select `.drawio` file
3. For each page: File → Export as → PNG
4. Configure: Border=10, Crop to Content
5. Download and save to this folder

### Option C: Command Line (if drawio-cli installed)
```bash
cd docs/Presentations/TemplateHierarchy-Fleet/
drawio-export schemas/01-fleet-architecture.drawio -f png -o images/
drawio-export schemas/02-template-hierarchy.drawio -f png -o images/
```
