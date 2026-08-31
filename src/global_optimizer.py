"""Optional network-flow relocation optimizer for comparison/research use.

Unlike the teammate prototype, this implementation only creates edges to shelters
that already pass the project's existing safety/capacity ranking gate. It also
keeps demo-city assignments local. A high-cost deficit edge makes shortages
explicit instead of making the optimization infeasible or overfilling shelters.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd

from src.relocation import rank_shelters


def optimize_relocation_flow(habitations: pd.DataFrame, shelters: pd.DataFrame, *, priorities=("IMMEDIATE", "SHORT_TERM")) -> dict:
    selected = habitations[habitations["relocation_priority"].astype(str).str.upper().isin({p.upper() for p in priorities})].copy()
    if selected.empty:
        return {"required_population": 0, "allocated_population": 0, "remaining_deficit": 0, "allocations": [], "method": "network_simplex"}

    shelter_records = shelters.to_dict(orient="records")
    total_population = int(pd.to_numeric(selected["population"], errors="coerce").fillna(0).clip(lower=0).sum())
    graph = nx.DiGraph()
    graph.add_node("SOURCE", demand=-total_population)
    graph.add_node("SINK", demand=total_population)
    graph.add_node("DEFICIT", demand=0)
    graph.add_edge("DEFICIT", "SINK", capacity=total_population, weight=0)

    shelter_capacity: dict[str, int] = {}
    for shelter in shelter_records:
        sid = str(shelter["shelter_id"])
        node = f"S::{sid}"
        available = max(0, int(float(shelter.get("available_capacity", 0) or 0)))
        shelter_capacity[sid] = available
        graph.add_node(node, demand=0)
        graph.add_edge(node, "SINK", capacity=available, weight=0)

    metadata: dict[tuple[str, str], dict] = {}
    for habitation in selected.to_dict(orient="records"):
        hid = str(habitation["habitation_id"])
        hnode = f"H::{hid}"
        population = max(0, int(float(habitation.get("population", 0) or 0)))
        graph.add_node(hnode, demand=0)
        graph.add_edge("SOURCE", hnode, capacity=population, weight=0)
        graph.add_edge(hnode, "DEFICIT", capacity=population, weight=100000)

        local = shelter_records
        if habitation.get("demo_city") and "demo_city" in shelters.columns:
            local = [s for s in shelter_records if s.get("demo_city") == habitation.get("demo_city")]
        for candidate in rank_shelters(habitation, local):
            sid = str(candidate["shelter_id"])
            snode = f"S::{sid}"
            # Minimize a transparent inverse-suitability cost. Safety/capacity have
            # already been enforced by rank_shelters before this edge exists.
            cost = max(0, int(round((100.0 - float(candidate["suitability_score"])) * 100)))
            graph.add_edge(hnode, snode, capacity=population, weight=cost)
            metadata[(hid, sid)] = candidate

    _, flow = nx.network_simplex(graph)
    allocations: list[dict] = []
    deficit = 0
    for habitation in selected.to_dict(orient="records"):
        hid = str(habitation["habitation_id"])
        hnode = f"H::{hid}"
        deficit += int(flow[hnode].get("DEFICIT", 0))
        for target, assigned in flow[hnode].items():
            if not target.startswith("S::") or assigned <= 0:
                continue
            sid = target.split("::", 1)[1]
            candidate = metadata[(hid, sid)]
            allocations.append({
                "habitation_id": hid,
                "habitation_name": habitation.get("name"),
                "demo_city": habitation.get("demo_city"),
                "shelter_id": sid,
                "shelter_name": candidate.get("shelter_name"),
                "assigned_population": int(assigned),
                "distance_km": candidate.get("distance_km"),
                "suitability_score": candidate.get("suitability_score"),
            })

    allocated = total_population - deficit
    return {
        "required_population": total_population,
        "allocated_population": allocated,
        "remaining_deficit": deficit,
        "allocations": allocations,
        "method": "network_simplex",
        "note": "Experimental comparison; uses only shelters that pass existing safety/capacity filters.",
    }
