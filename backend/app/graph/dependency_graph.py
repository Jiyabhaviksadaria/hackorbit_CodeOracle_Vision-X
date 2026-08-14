"""
Dependency graph builder — Phase 4.
Owned by API/Integration Engineer.

Consumes ParsedChunks (calls/imports fields) from Backend parsing
and emits DepGraph schema exactly as defined in CONTRACT.md.
"""
from typing import List, Dict, Set
from ..models.contract import ParsedChunk, DepGraph


def build_dep_graph(chunks: List[ParsedChunk]) -> DepGraph:
    """
    Build a dependency graph from parsed chunks.

    Nodes  → every function/class/module chunk
    Edges  → call relationships (chunk.calls) + import relationships

    CONTRACT.md schema:
      nodes: [{ id, label, file }]
      edges: [{ source, target }]

    Args:
        chunks: List of ParsedChunk from Backend parsing stage.

    Returns:
        DepGraph — always valid, never None. Empty graph when no chunks.
    """
    if not chunks:
        return DepGraph(nodes=[], edges=[])

    nodes: List[Dict] = []
    edges: List[Dict] = []
    seen_node_ids: Set[str] = set()

    # Index: name → node_id  (for resolving call targets)
    name_to_node_id: Dict[str, str] = {}

    # ── Pass 1: build nodes ──────────────────────────────────────────
    for chunk in chunks:
        node_id = f"{chunk.file}::{chunk.name}"

        if node_id not in seen_node_ids:
            nodes.append({
                "id": node_id,
                "label": chunk.name,
                "file": chunk.file,
                "type": chunk.type,
                "language": chunk.language,
            })
            seen_node_ids.add(node_id)
            # Map bare name → full id (last write wins for now; good enough for demo)
            name_to_node_id[chunk.name] = node_id

    # ── Pass 2: build edges from calls ───────────────────────────────
    seen_edges: Set[tuple] = set()

    for chunk in chunks:
        source_id = f"{chunk.file}::{chunk.name}"

        for call in chunk.calls:
            target_id = name_to_node_id.get(call)
            if target_id and target_id != source_id:
                edge_key = (source_id, target_id)
                if edge_key not in seen_edges:
                    edges.append({"source": source_id, "target": target_id})
                    seen_edges.add(edge_key)

        # Also add import-level edges (module → imported module node if present)
        for imp in chunk.imports:
            target_id = name_to_node_id.get(imp)
            if target_id and target_id != source_id:
                edge_key = (source_id, target_id)
                if edge_key not in seen_edges:
                    edges.append({"source": source_id, "target": target_id})
                    seen_edges.add(edge_key)

    return DepGraph(nodes=nodes, edges=edges)
