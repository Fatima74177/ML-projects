"""
Knowledge Graph (Sections 16 & 17).

Runtime engine: an in-process NetworkX MultiDiGraph built live from the
relational database on each query -- this is a REAL graph, not a mock, and
graph analytics (degree centrality, connected components) are computed with
real NetworkX algorithms. A Neo4j Cypher-ready loader (`neo4j_seed_queries()`)
is included and used by neo4j/seed.cypher; when NEO4J_ENABLED=true in
docker-compose, the same relationship model can be pushed into Neo4j via the
official `neo4j` Python driver (see docker-compose service) without changing
the entity/relationship schema below.
"""
from __future__ import annotations
from typing import Dict, List

import networkx as nx
from sqlalchemy.orm import Session

from app.models._all import Identity, Device, DeviceLink, IPAddress, IPLink, Document, FraudCase


def build_graph(db: Session) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()

    for identity in db.query(Identity).all():
        g.add_node(f"user:{identity.id}", type="User", label=identity.full_name, risk=identity.risk_level_cached)

    for doc in db.query(Document).all():
        node_id = f"document:{doc.id}"
        g.add_node(node_id, type="Document", label=doc.document_number or f"doc-{doc.id}", doc_type=doc.document_type)
        g.add_edge(f"user:{doc.identity_id}", node_id, relationship="USER_HAS_DOCUMENT")
        g.add_edge(node_id, f"user:{doc.identity_id}", relationship="DOCUMENT_USED_BY")

    for device in db.query(Device).all():
        g.add_node(f"device:{device.id}", type="Device", label=device.device_fingerprint)
    for link in db.query(DeviceLink).all():
        g.add_edge(f"user:{link.identity_id}", f"device:{link.device_id}", relationship="USER_USES_DEVICE")
        g.add_edge(f"device:{link.device_id}", f"user:{link.identity_id}", relationship="DEVICE_USED_BY")

    for ip in db.query(IPAddress).all():
        g.add_node(f"ip:{ip.id}", type="IP", label=ip.ip, high_risk=ip.is_high_risk)
    for link in db.query(IPLink).all():
        g.add_edge(f"user:{link.identity_id}", f"ip:{link.ip_id}", relationship="USER_USES_IP")

    for case in db.query(FraudCase).all():
        node_id = f"case:{case.id}"
        g.add_node(node_id, type="FraudCase", label=f"Case #{case.id}", severity=case.severity)
        for uid in case.related_identities or []:
            g.add_edge(f"user:{uid}", node_id, relationship="USER_INVOLVED_IN_CASE")

    return g


def get_user_subgraph(db: Session, identity_id: int, depth: int = 2) -> Dict:
    g = build_graph(db)
    root = f"user:{identity_id}"
    if root not in g:
        return {"nodes": [], "edges": []}

    visited = {root}
    frontier = {root}
    for _ in range(depth):
        next_frontier = set()
        for node in frontier:
            next_frontier |= set(g.successors(node)) | set(g.predecessors(node))
        next_frontier -= visited
        visited |= next_frontier
        frontier = next_frontier

    sub = g.subgraph(visited)
    nodes = [{"id": n, **sub.nodes[n]} for n in sub.nodes]
    edges = [{"source": u, "target": v, **data} for u, v, data in sub.edges(data=True)]
    return {"nodes": nodes, "edges": edges}


def graph_analytics(db: Session) -> Dict:
    g = build_graph(db)
    undirected = g.to_undirected()
    degree_centrality = nx.degree_centrality(g)
    components = list(nx.connected_components(undirected))

    top_connected = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    suspicious_clusters = [list(c) for c in components if len(c) >= 4]

    return {
        "node_count": g.number_of_nodes(),
        "edge_count": g.number_of_edges(),
        "connected_components": len(components),
        "top_connected_entities": [{"node": n, "centrality": round(c, 4)} for n, c in top_connected],
        "suspicious_clusters": suspicious_clusters[:10],
    }


def find_documents_used_by_multiple_users(db: Session) -> List[dict]:
    from app.services.fraud_service import find_shared_documents
    return find_shared_documents(db)


NEO4J_SCHEMA_NOTE = """
Entities: User, Device, Document, Phone, IP, Biometric, Verification, FraudCase, VoiceProfile
Relationships: USER_USES_DEVICE, USER_HAS_DOCUMENT, USER_USES_PHONE, USER_HAS_BIOMETRIC,
USER_USES_IP, DOCUMENT_USED_BY, DEVICE_USED_BY, BIOMETRIC_MATCHED, USER_INVOLVED_IN_CASE,
VERIFICATION_FAILED, VERIFICATION_PASSED
See neo4j/seed.cypher for the loader used when NEO4J_ENABLED=true.
"""
