"""Export full public knowledge graph to standard formats (CSV, GEXF, VOSviewer JSON).

Usable with:
- Cosmograph (https://cosmograph.app/run)
- Gephi (https://gephi.org)
- VOSviewer Online (https://app.vosviewer.com)
- Cytoscape (https://cytoscape.org)
"""

import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

def export_all():
    api_url = "http://127.0.0.1:18088/api/v2/graph?limit=3000"
    print(f"Fetching full corpus graph from {api_url}...")
    
    try:
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching from API: {e}")
        sys.exit(1)

    nodes = data.get('nodes', [])
    links = data.get('links', [])
    print(f"Loaded {len(nodes)} nodes and {len(links)} links.")

    out_dir = Path("data/viz")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Export nodes.csv & edges.csv (Standard for Cosmograph, Gephi, Kumu)
    nodes_csv_path = out_dir / "nodes.csv"
    with open(nodes_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "label", "type", "cluster", "degree", "color"])
        for n in nodes:
            writer.writerow([
                n.get('id', ''),
                n.get('name', ''),
                n.get('type', ''),
                n.get('cluster', ''),
                n.get('degree', 0),
                n.get('cluster_color', '#64748b'),
            ])
    print(f"Exported: {nodes_csv_path}")

    edges_csv_path = out_dir / "edges.csv"
    with open(edges_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "relationship", "evidence"])
        for l in links:
            writer.writerow([
                l.get('source', ''),
                l.get('target', ''),
                l.get('relationship', ''),
                l.get('evidence', ''),
            ])
    print(f"Exported: {edges_csv_path}")

    # 2. Export VOSviewer format JSON (for app.vosviewer.com)
    vos_items = []
    node_id_to_idx = {}
    for idx, n in enumerate(nodes, start=1):
        node_id_to_idx[n['id']] = idx
        vos_items.append({
            "id": idx,
            "label": n.get('name', ''),
            "cluster": n.get('cluster', 'General'),
            "score": n.get('degree', 1),
        })

    vos_links = []
    for l in links:
        s_idx = node_id_to_idx.get(l['source'])
        t_idx = node_id_to_idx.get(l['target'])
        if s_idx and t_idx:
            vos_links.append({
                "source_id": s_idx,
                "target_id": t_idx,
                "strength": 1,
            })

    vos_data = {
        "network": {
            "items": vos_items,
            "links": vos_links,
        }
    }
    vos_json_path = out_dir / "vosviewer_network.json"
    with open(vos_json_path, 'w', encoding='utf-8') as f:
        json.dump(vos_data, f, indent=2)
    print(f"Exported: {vos_json_path}")

    print("\nDone! You can now:")
    print("1. Drag 'nodes.csv' & 'edges.csv' into Cosmograph (https://cosmograph.app/run)")
    print("2. Open 'vosviewer_network.json' at https://app.vosviewer.com")
    print("3. Import 'nodes.csv' & 'edges.csv' into Gephi (File -> Import Spreadsheet)")

if __name__ == "__main__":
    export_all()
