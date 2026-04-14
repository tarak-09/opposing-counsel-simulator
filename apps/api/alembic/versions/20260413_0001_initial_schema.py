from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


document_role_enum = sa.Enum("original", "revised", "evidence", name="documentrole", native_enum=False)
document_type_enum = sa.Enum(
    "contract",
    "playbook",
    "precedent",
    "fallback",
    "benchmark",
    name="documenttype",
    native_enum=False,
)
source_kind_enum = sa.Enum("file", "text", name="sourcekind", native_enum=False)
parser_status_enum = sa.Enum("pending", "parsed", "failed", name="parserstatus", native_enum=False)
clause_change_type_enum = sa.Enum("added", "removed", "modified", name="clausechangetype", native_enum=False)
change_direction_enum = sa.Enum(
    "vendor_favorable",
    "customer_favorable",
    "mutual_or_neutral",
    "unknown",
    name="changedirection",
    native_enum=False,
)
issue_type_enum = sa.Enum(
    "limitation_of_liability",
    "indemnity",
    "confidentiality",
    "ip_ownership",
    "payment_terms",
    "warranties",
    "termination",
    "data_protection",
    "security",
    "governing_law",
    "service_levels",
    "audit_rights",
    "general",
    name="issuetype",
    native_enum=False,
)
run_status_enum = sa.Enum("queued", "processing", "completed", "failed", name="runstatus", native_enum=False)
simulation_decision_enum = sa.Enum(
    "accept", "push_back", "counter", "escalate", name="simulationdecision", native_enum=False
)


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", document_role_enum, nullable=False),
        sa.Column("document_type", document_type_enum, nullable=False),
        sa.Column("source_kind", source_kind_enum, nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_table(
        "personas",
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_tolerance", sa.Integer(), nullable=False),
        sa.Column("leverage", sa.Integer(), nullable=False),
        sa.Column("speed_priority", sa.Integer(), nullable=False),
        sa.Column("privacy_sensitivity", sa.Integer(), nullable=False),
        sa.Column("liability_strictness", sa.Integer(), nullable=False),
        sa.Column("fallback_flexibility", sa.Integer(), nullable=False),
        sa.Column("tone", sa.String(length=120), nullable=False),
        sa.Column("issue_positions", sa.JSON(), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_personas")),
        sa.UniqueConstraint("slug", name=op.f("uq_personas_slug")),
    )
    op.create_index(op.f("ix_personas_slug"), "personas", ["slug"], unique=False)
    op.create_table(
        "document_versions",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("raw_text_input", sa.Text(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("section_map", sa.JSON(), nullable=False),
        sa.Column("parser_status", parser_status_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_versions_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_versions")),
    )
    op.create_index(op.f("ix_document_versions_document_id"), "document_versions", ["document_id"], unique=False)
    op.create_index(
        "ix_document_versions_document_id_version_number",
        "document_versions",
        ["document_id", "version_number"],
        unique=False,
    )
    op.create_table(
        "negotiation_runs",
        sa.Column("original_document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revised_document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", run_status_enum, nullable=False),
        sa.Column("stage", sa.String(length=120), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("total_changed_clauses", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["original_document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_negotiation_runs_original_document_version_id_document_versions"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["persona_id"],
            ["personas.id"],
            name=op.f("fk_negotiation_runs_persona_id_personas"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["revised_document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_negotiation_runs_revised_document_version_id_document_versions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_negotiation_runs")),
    )
    op.create_index(
        op.f("ix_negotiation_runs_original_document_version_id"),
        "negotiation_runs",
        ["original_document_version_id"],
        unique=False,
    )
    op.create_index(op.f("ix_negotiation_runs_persona_id"), "negotiation_runs", ["persona_id"], unique=False)
    op.create_index(
        op.f("ix_negotiation_runs_revised_document_version_id"),
        "negotiation_runs",
        ["revised_document_version_id"],
        unique=False,
    )
    op.create_index("ix_negotiation_runs_status_stage", "negotiation_runs", ["status", "stage"], unique=False)
    op.create_table(
        "clauses",
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stable_clause_id", sa.String(length=120), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=False),
        sa.Column("heading_path", sa.String(length=500), nullable=False),
        sa.Column("clause_number", sa.String(length=64), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("source_span", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], name=op.f("fk_clauses_document_version_id_document_versions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clauses")),
    )
    op.create_index(op.f("ix_clauses_document_version_id"), "clauses", ["document_version_id"], unique=False)
    op.create_index(
        "ix_clauses_document_version_id_order_index",
        "clauses",
        ["document_version_id", "order_index"],
        unique=False,
    )
    op.create_index(
        "ix_clauses_document_version_id_stable_clause_id",
        "clauses",
        ["document_version_id", "stable_clause_id"],
        unique=False,
    )
    op.create_table(
        "evidence_sources",
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_type", document_type_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("section_label", sa.String(length=255), nullable=False),
        sa.Column("snippet_text", sa.Text(), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("vector_id", sa.String(length=120), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], name=op.f("fk_evidence_sources_document_version_id_document_versions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_sources")),
    )
    op.create_index(op.f("ix_evidence_sources_document_version_id"), "evidence_sources", ["document_version_id"], unique=False)
    op.create_index(
        "ix_evidence_sources_document_version_id_title",
        "evidence_sources",
        ["document_version_id", "title"],
        unique=False,
    )
    op.create_table(
        "clause_changes",
        sa.Column("negotiation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_clause_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revised_clause_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("clause_key", sa.String(length=120), nullable=False),
        sa.Column("change_type", clause_change_type_enum, nullable=False),
        sa.Column("issue_type", issue_type_enum, nullable=False),
        sa.Column("change_direction", change_direction_enum, nullable=False),
        sa.Column("semantic_summary", sa.Text(), nullable=False),
        sa.Column("diff_details", sa.JSON(), nullable=False),
        sa.Column("changed_tokens_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["negotiation_run_id"], ["negotiation_runs.id"], name=op.f("fk_clause_changes_negotiation_run_id_negotiation_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["original_clause_id"], ["clauses.id"], name=op.f("fk_clause_changes_original_clause_id_clauses"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["revised_clause_id"], ["clauses.id"], name=op.f("fk_clause_changes_revised_clause_id_clauses"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clause_changes")),
    )
    op.create_index(op.f("ix_clause_changes_negotiation_run_id"), "clause_changes", ["negotiation_run_id"], unique=False)
    op.create_index("ix_clause_changes_run_id_clause_key", "clause_changes", ["negotiation_run_id", "clause_key"], unique=False)
    op.create_index("ix_clause_changes_run_id_issue_type", "clause_changes", ["negotiation_run_id", "issue_type"], unique=False)
    op.create_table(
        "retrieval_hits",
        sa.Column("negotiation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_change_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("vector_score", sa.Float(), nullable=False),
        sa.Column("lexical_score", sa.Float(), nullable=False),
        sa.Column("rerank_score", sa.Float(), nullable=False),
        sa.Column("snippet_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clause_change_id"], ["clause_changes.id"], name=op.f("fk_retrieval_hits_clause_change_id_clause_changes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_source_id"], ["evidence_sources.id"], name=op.f("fk_retrieval_hits_evidence_source_id_evidence_sources"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["negotiation_run_id"], ["negotiation_runs.id"], name=op.f("fk_retrieval_hits_negotiation_run_id_negotiation_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_hits")),
    )
    op.create_index(op.f("ix_retrieval_hits_clause_change_id"), "retrieval_hits", ["clause_change_id"], unique=False)
    op.create_index(op.f("ix_retrieval_hits_evidence_source_id"), "retrieval_hits", ["evidence_source_id"], unique=False)
    op.create_index(op.f("ix_retrieval_hits_negotiation_run_id"), "retrieval_hits", ["negotiation_run_id"], unique=False)
    op.create_index("ix_retrieval_hits_run_clause_rank", "retrieval_hits", ["negotiation_run_id", "clause_change_id", "rank"], unique=False)
    op.create_table(
        "simulation_results",
        sa.Column("negotiation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_change_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", simulation_decision_enum, nullable=False),
        sa.Column("stance_strength", sa.Integer(), nullable=False),
        sa.Column("business_reason", sa.Text(), nullable=False),
        sa.Column("legal_reason", sa.Text(), nullable=False),
        sa.Column("pushback_points", sa.JSON(), nullable=False),
        sa.Column("counterproposal_text", sa.Text(), nullable=False),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("critique_status", sa.String(length=50), nullable=False),
        sa.Column("grounded_evidence_count", sa.Integer(), nullable=False),
        sa.Column("raw_model_output", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clause_change_id"], ["clause_changes.id"], name=op.f("fk_simulation_results_clause_change_id_clause_changes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["negotiation_run_id"], ["negotiation_runs.id"], name=op.f("fk_simulation_results_negotiation_run_id_negotiation_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_simulation_results")),
        sa.UniqueConstraint("clause_change_id", name=op.f("uq_simulation_results_clause_change_id")),
    )
    op.create_index(op.f("ix_simulation_results_clause_change_id"), "simulation_results", ["clause_change_id"], unique=False)
    op.create_index(op.f("ix_simulation_results_negotiation_run_id"), "simulation_results", ["negotiation_run_id"], unique=False)
    op.create_index("ix_simulation_results_run_clause", "simulation_results", ["negotiation_run_id", "clause_change_id"], unique=False)
    op.create_table(
        "scoring_results",
        sa.Column("negotiation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_change_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pushback_probability", sa.Float(), nullable=False),
        sa.Column("negotiation_friction", sa.Float(), nullable=False),
        sa.Column("delay_risk", sa.Float(), nullable=False),
        sa.Column("severity", sa.Float(), nullable=False),
        sa.Column("friction_label", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("heuristic_details", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clause_change_id"], ["clause_changes.id"], name=op.f("fk_scoring_results_clause_change_id_clause_changes"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["negotiation_run_id"], ["negotiation_runs.id"], name=op.f("fk_scoring_results_negotiation_run_id_negotiation_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scoring_results")),
        sa.UniqueConstraint("clause_change_id", name=op.f("uq_scoring_results_clause_change_id")),
    )
    op.create_index(op.f("ix_scoring_results_clause_change_id"), "scoring_results", ["clause_change_id"], unique=False)
    op.create_index(op.f("ix_scoring_results_negotiation_run_id"), "scoring_results", ["negotiation_run_id"], unique=False)
    op.create_index("ix_scoring_results_run_clause", "scoring_results", ["negotiation_run_id", "clause_change_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scoring_results_run_clause", table_name="scoring_results")
    op.drop_index(op.f("ix_scoring_results_negotiation_run_id"), table_name="scoring_results")
    op.drop_index(op.f("ix_scoring_results_clause_change_id"), table_name="scoring_results")
    op.drop_table("scoring_results")
    op.drop_index("ix_simulation_results_run_clause", table_name="simulation_results")
    op.drop_index(op.f("ix_simulation_results_negotiation_run_id"), table_name="simulation_results")
    op.drop_index(op.f("ix_simulation_results_clause_change_id"), table_name="simulation_results")
    op.drop_table("simulation_results")
    op.drop_index("ix_retrieval_hits_run_clause_rank", table_name="retrieval_hits")
    op.drop_index(op.f("ix_retrieval_hits_negotiation_run_id"), table_name="retrieval_hits")
    op.drop_index(op.f("ix_retrieval_hits_evidence_source_id"), table_name="retrieval_hits")
    op.drop_index(op.f("ix_retrieval_hits_clause_change_id"), table_name="retrieval_hits")
    op.drop_table("retrieval_hits")
    op.drop_index("ix_clause_changes_run_id_issue_type", table_name="clause_changes")
    op.drop_index("ix_clause_changes_run_id_clause_key", table_name="clause_changes")
    op.drop_index(op.f("ix_clause_changes_negotiation_run_id"), table_name="clause_changes")
    op.drop_table("clause_changes")
    op.drop_index("ix_evidence_sources_document_version_id_title", table_name="evidence_sources")
    op.drop_index(op.f("ix_evidence_sources_document_version_id"), table_name="evidence_sources")
    op.drop_table("evidence_sources")
    op.drop_index("ix_clauses_document_version_id_stable_clause_id", table_name="clauses")
    op.drop_index("ix_clauses_document_version_id_order_index", table_name="clauses")
    op.drop_index(op.f("ix_clauses_document_version_id"), table_name="clauses")
    op.drop_table("clauses")
    op.drop_index("ix_negotiation_runs_status_stage", table_name="negotiation_runs")
    op.drop_index(op.f("ix_negotiation_runs_revised_document_version_id"), table_name="negotiation_runs")
    op.drop_index(op.f("ix_negotiation_runs_persona_id"), table_name="negotiation_runs")
    op.drop_index(op.f("ix_negotiation_runs_original_document_version_id"), table_name="negotiation_runs")
    op.drop_table("negotiation_runs")
    op.drop_index("ix_document_versions_document_id_version_number", table_name="document_versions")
    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index(op.f("ix_personas_slug"), table_name="personas")
    op.drop_table("personas")
    op.drop_table("documents")
