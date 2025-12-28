import uuid
from typing import Any
from datetime import datetime

from sqlalchemy import (
    UniqueConstraint,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Float,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from .base import Base


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # NOTE: updated_at is maintained in app code for v0 (no DB triggers yet).


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        CheckConstraint(
            "ingestion_status IN ('queued','running','succeeded','failed')",
            name="artifacts_ingestion_status_check",
        ),
        CheckConstraint(
            "artifact_kind IN ('doc','code','repo_map','resume')",
            name="artifacts_artifact_kind_check",
        ),
        Index("artifacts_folder_id_idx", "folder_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(Text, nullable=False)

    storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)

    file_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    artifact_kind: Mapped[str] = mapped_column(Text, nullable=False)

    ingestion_status: Mapped[str] = mapped_column(Text, nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    extracted_text_preview: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # NOTE: updated_at is maintained in app code for v0 (no DB triggers yet).


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint(
            "artifact_id", "chunk_index", name="chunks_artifact_id_chunk_index_key"
        ),
        Index("chunks_artifact_id_idx", "artifact_id"),
    )

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    locator: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        primary_key=True,
    )

    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    model_name: Mapped[str] = mapped_column(Text, nullable=False)

    model_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Run(Base):
    __tablename__ = "runs"

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    kind: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    scope_folder_ids: Mapped[list[uuid.UUID]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )

    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    embed_model: Mapped[str | None] = mapped_column(Text, nullable=True)


class RunRetrievedChunk(Base):
    __tablename__ = "run_retrieved_chunks"
    __table_args__ = (
        PrimaryKeyConstraint("trace_id", "rank", name="run_retrieved_chunks_pkey"),
        UniqueConstraint("trace_id", "chunk_id", name="rrc_trace_id_chunk_id_key"),
        Index("rrc_trace_id_idx", "trace_id"),
    )

    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.trace_id", ondelete="CASCADE"),
        nullable=False,
    )

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(Float, nullable=False)

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
