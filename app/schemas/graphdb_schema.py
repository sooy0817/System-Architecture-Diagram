from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Types of entities in the graph database"""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    TECHNOLOGY = "technology"
    PROCESS = "process"
    DOCUMENT = "document"
    SYSTEM = "system"


class RelationshipType(str, Enum):
    """Types of relationships in the graph database"""

    WORKS_AT = "works_at"
    LOCATED_IN = "located_in"
    USES = "uses"
    CONNECTS_TO = "connects_to"
    MANAGES = "manages"
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    IMPLEMENTS = "implements"


class GraphEntity(BaseModel):
    """Entity in the graph database"""

    id: str = Field(..., description="Unique entity identifier")
    type: EntityType = Field(..., description="Entity type")
    name: str = Field(..., description="Entity name")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Entity properties"
    )
    labels: List[str] = Field(default_factory=list, description="Entity labels")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    version: int = Field(default=1, description="Entity version")


class GraphRelationship(BaseModel):
    """Relationship in the graph database"""

    id: str = Field(..., description="Unique relationship identifier")
    type: RelationshipType = Field(..., description="Relationship type")
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )
    weight: float = Field(default=1.0, description="Relationship weight")
    confidence: float = Field(default=1.0, description="Confidence score")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class GraphPath(BaseModel):
    """Path in the graph database"""

    id: str = Field(..., description="Path identifier")
    entities: List[GraphEntity] = Field(..., description="Entities in the path")
    relationships: List[GraphRelationship] = Field(
        ..., description="Relationships in the path"
    )
    length: int = Field(..., description="Path length")
    total_weight: float = Field(..., description="Total path weight")


class GraphQuery(BaseModel):
    """Query for the graph database"""

    query_type: str = Field(..., description="Type of query (cypher, gremlin, sparql)")
    query_string: str = Field(..., description="Query string")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Query parameters"
    )
    limit: Optional[int] = Field(None, description="Result limit")
    offset: Optional[int] = Field(None, description="Result offset")


class GraphQueryResult(BaseModel):
    """Result of a graph query"""

    query_id: str = Field(..., description="Query identifier")
    entities: List[GraphEntity] = Field(
        default_factory=list, description="Resulting entities"
    )
    relationships: List[GraphRelationship] = Field(
        default_factory=list, description="Resulting relationships"
    )
    paths: List[GraphPath] = Field(default_factory=list, description="Resulting paths")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Query metadata")
    execution_time: float = Field(..., description="Query execution time")
    total_results: int = Field(..., description="Total number of results")


class GraphSchema(BaseModel):
    """Schema definition for the graph database"""

    entity_types: List[EntityType] = Field(..., description="Supported entity types")
    relationship_types: List[RelationshipType] = Field(
        ..., description="Supported relationship types"
    )
    constraints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Schema constraints"
    )
    indexes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Database indexes"
    )
    version: str = Field(..., description="Schema version")


class GraphStatistics(BaseModel):
    """Statistics about the graph database"""

    total_entities: int = Field(..., description="Total number of entities")
    total_relationships: int = Field(..., description="Total number of relationships")
    entity_counts: Dict[str, int] = Field(..., description="Count by entity type")
    relationship_counts: Dict[str, int] = Field(
        ..., description="Count by relationship type"
    )
    average_degree: float = Field(..., description="Average node degree")
    density: float = Field(..., description="Graph density")
    connected_components: int = Field(..., description="Number of connected components")
    diameter: Optional[int] = Field(None, description="Graph diameter")


class GraphTransaction(BaseModel):
    """Transaction for graph operations"""

    transaction_id: str = Field(..., description="Transaction identifier")
    operations: List[Dict[str, Any]] = Field(
        ..., description="Operations in the transaction"
    )
    status: str = Field(default="pending", description="Transaction status")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Transaction creation time"
    )
    committed_at: Optional[datetime] = Field(
        None, description="Transaction commit time"
    )
    rolled_back_at: Optional[datetime] = Field(
        None, description="Transaction rollback time"
    )


class GraphBackup(BaseModel):
    """Graph database backup"""

    backup_id: str = Field(..., description="Backup identifier")
    backup_type: str = Field(..., description="Backup type (full, incremental)")
    file_path: str = Field(..., description="Backup file path")
    size_bytes: int = Field(..., description="Backup size in bytes")
    entity_count: int = Field(..., description="Number of entities backed up")
    relationship_count: int = Field(
        ..., description="Number of relationships backed up"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Backup creation time"
    )
    checksum: str = Field(..., description="Backup checksum")


class GraphImport(BaseModel):
    """Graph data import configuration"""

    import_id: str = Field(..., description="Import identifier")
    source_type: str = Field(..., description="Source type (csv, json, xml, rdf)")
    source_path: str = Field(..., description="Source file path")
    mapping_config: Dict[str, Any] = Field(
        ..., description="Data mapping configuration"
    )
    validation_rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="Validation rules"
    )
    batch_size: int = Field(default=1000, description="Import batch size")
    status: str = Field(default="pending", description="Import status")
    progress: float = Field(default=0.0, description="Import progress (0-100)")
    errors: List[str] = Field(default_factory=list, description="Import errors")


class GraphExport(BaseModel):
    """Graph data export configuration"""

    export_id: str = Field(..., description="Export identifier")
    target_format: str = Field(
        ..., description="Target format (csv, json, xml, rdf, graphml)"
    )
    target_path: str = Field(..., description="Target file path")
    filter_config: Dict[str, Any] = Field(
        default_factory=dict, description="Export filter configuration"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in export"
    )
    compression: Optional[str] = Field(None, description="Compression type")
    status: str = Field(default="pending", description="Export status")
    progress: float = Field(default=0.0, description="Export progress (0-100)")
    file_size: Optional[int] = Field(None, description="Exported file size")
