"""Initial Migrate

Revision ID: 7936cecf1591
Revises: 455dde5ecaa6
Create Date: 2025-04-01 14:18:49.950716

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
import pgvector

# revision identifiers, used by Alembic.
revision = '7936cecf1591'
down_revision = '455dde5ecaa6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('document',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('upload_id', sa.Uuid(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('text_content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
    sa.ForeignKeyConstraint(['upload_id'], ['upload.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_id'), 'document', ['id'], unique=False)
    op.drop_index('ix_vectordocument_id', table_name='vectordocument')
    op.drop_table('vectordocument')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vectordocument',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('upload_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), autoincrement=False, nullable=True),
    sa.Column('chunk_index', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('text_content', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['upload_id'], ['upload.id'], name='vectordocument_upload_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='vectordocument_pkey')
    )
    op.create_index('ix_vectordocument_id', 'vectordocument', ['id'], unique=False)
    op.drop_index(op.f('ix_document_id'), table_name='document')
    op.drop_table('document')
    # ### end Alembic commands ###
