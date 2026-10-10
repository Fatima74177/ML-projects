// EEF Knowledge Graph schema + example seed (Section 16).
// Run with: cat neo4j/seed.cypher | cypher-shell -u neo4j -p <password>
// or via the Neo4j Browser at http://localhost:7474 when NEO4J_ENABLED=true.
//
// This mirrors the same entity/relationship model the in-process NetworkX
// engine builds live from Postgres (see backend/app/services/graph_service.py).
// When NEO4J_ENABLED=true, a background sync job (workers/) can push the same
// rows here via the official `neo4j` Python driver without changing the schema.

// --- Constraints -------------------------------------------------------
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (doc:Document) REQUIRE doc.id IS UNIQUE;
CREATE CONSTRAINT ip_id IF NOT EXISTS FOR (i:IP) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:FraudCase) REQUIRE c.id IS UNIQUE;

// --- Example seed nodes (illustrative -- real sync populates from Postgres) --
MERGE (u1:User {id: 1, name: 'Amina Khan', risk: 'MEDIUM'});
MERGE (u2:User {id: 2, name: 'John Smith', risk: 'HIGH'});
MERGE (u3:User {id: 3, name: 'Fatima Ali', risk: 'CRITICAL'});

MERGE (d1:Device {id: 1, fingerprint: 'DEV-FP-0000'});
MERGE (doc1:Document {id: 1, number: 'ID-SHARED-99001', type: 'NATIONAL_ID'});
MERGE (ip1:IP {id: 1, address: '10.20.0.0', high_risk: true});
MERGE (case1:FraudCase {id: 1, severity: 'MEDIUM', status: 'OPEN'});

MERGE (u1)-[:USER_USES_DEVICE]->(d1);
MERGE (u2)-[:USER_USES_DEVICE]->(d1);
MERGE (u3)-[:USER_USES_DEVICE]->(d1);
MERGE (d1)-[:DEVICE_USED_BY]->(u1);

MERGE (u1)-[:USER_HAS_DOCUMENT]->(doc1);
MERGE (u2)-[:USER_HAS_DOCUMENT]->(doc1);
MERGE (doc1)-[:DOCUMENT_USED_BY]->(u1);
MERGE (doc1)-[:DOCUMENT_USED_BY]->(u2);

MERGE (u1)-[:USER_USES_IP]->(ip1);
MERGE (u2)-[:USER_USES_IP]->(ip1);

MERGE (u1)-[:USER_INVOLVED_IN_CASE]->(case1);
MERGE (u2)-[:USER_INVOLVED_IN_CASE]->(case1);

// --- Example analytical queries ----------------------------------------
// Find all users connected to a device:
// MATCH (u:User)-[:USER_USES_DEVICE]->(d:Device {id: 1}) RETURN u;
//
// Find documents used by multiple users:
// MATCH (doc:Document)-[:DOCUMENT_USED_BY]->(u:User)
// WITH doc, count(DISTINCT u) AS n WHERE n > 1 RETURN doc, n;
//
// Find suspicious identity clusters (users sharing 2+ of device/doc/ip):
// MATCH (u1:User)-[:USER_USES_DEVICE]->(d:Device)<-[:USER_USES_DEVICE]-(u2:User)
// WHERE u1.id <> u2.id RETURN DISTINCT u1, u2, d;
