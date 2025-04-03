"""Initial Migrate

Revision ID: 3b3e02de5504
Revises: 6b20ac4e7825
Create Date: 2025-04-03 01:50:05.848802

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '3b3e02de5504'
down_revision = '6b20ac4e7825'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('embedding', 'owner_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.alter_column('embedding', 'team_id',
               existing_type=sa.UUID(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('embedding', 'team_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.alter_column('embedding', 'owner_id',
               existing_type=sa.UUID(),
               nullable=True)
    # ### end Alembic commands ###
