from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_viewer
from app.services import graph_service

router = APIRouter()


@router.get("/user/{identity_id}", summary="Get the relationship graph around an identity",
            description="Returns nodes and edges (User, Document, Device, IP, FraudCase) connected to this "
                        "identity within a configurable traversal depth. Built live from the relational database "
                        "via NetworkX; ready to swap in a Neo4j-backed traversal (see neo4j/seed.cypher).")
def user_graph(identity_id: int, depth: int = 2, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    return graph_service.get_user_subgraph(db, identity_id, depth)


@router.get("/analytics", summary="Run graph analytics (centrality, connected components, suspicious clusters)")
def analytics(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    return graph_service.graph_analytics(db)


@router.get("/shared-documents", summary="Find documents used by more than one identity")
def shared_documents(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    return graph_service.find_documents_used_by_multiple_users(db)
