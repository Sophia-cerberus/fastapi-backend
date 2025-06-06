"""initial migrate

Revision ID: e268f2728db0
Revises: 
Create Date: 2025-05-11 14:38:30.237179

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e268f2728db0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dictionaries',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dictionaries_id'), 'dictionaries', ['id'], unique=False)
    op.create_index(op.f('ix_dictionaries_name'), 'dictionaries', ['name'], unique=True)
    op.create_table('invite_codes',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('code', name='unique_invite_code')
    )
    op.create_index(op.f('ix_invite_codes_id'), 'invite_codes', ['id'], unique=False)
    op.create_table('dictionary_arguments',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('label', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('value', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=False),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.Column('sort', sa.Integer(), nullable=False),
    sa.Column('dict_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['dict_id'], ['dictionaries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dictionary_arguments_id'), 'dictionary_arguments', ['id'], unique=False)
    op.create_table('tenant',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('plan', sa.Enum('FREE', 'BASIC', 'PROFESSIONAL', 'ENTERPRISE', name='tenantplan'), nullable=False),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.Column('dictionaries', sa.Uuid(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('public_key', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['dictionaries'], ['dictionaries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_id'), 'tenant', ['id'], unique=False)
    op.create_index(op.f('ix_tenant_name'), 'tenant', ['name'], unique=True)
    op.create_table('user',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('avatar', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_tenant_admin', sa.Boolean(), nullable=False),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('dictionaries', sa.Uuid(), nullable=True),
    sa.Column('corporate_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('industry_affiliation', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('business_scenarios', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('language', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['dictionaries'], ['dictionaries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_phone'), 'user', ['phone'], unique=True)
    op.create_table('team',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('icon', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_team_id'), 'team', ['id'], unique=False)
    op.create_table('apikey',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('hashed_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('short_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apikey_id'), 'apikey', ['id'], unique=False)
    op.create_table('dataset',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('parent_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dataset_cmetadata_gin', 'dataset', ['cmetadata'], unique=False, postgresql_using='gin', postgresql_ops={'cmetadata': 'jsonb_path_ops'})
    op.create_index(op.f('ix_dataset_id'), 'dataset', ['id'], unique=False)
    op.create_index(op.f('ix_dataset_name'), 'dataset', ['name'], unique=False)
    op.create_table('graph',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('parent', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['parent'], ['graph.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_graph_id'), 'graph', ['id'], unique=False)
    op.create_index(op.f('ix_graph_parent'), 'graph', ['parent'], unique=False)
    op.create_table('modelprovider',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('provider_name', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('base_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('api_key', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('icon', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_modelprovider_id'), 'modelprovider', ['id'], unique=False)
    op.create_table('team_user_join',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.Enum('MEMBER', 'MODERATOR', 'ADMIN', 'OWNER', name='roletypes'), nullable=False),
    sa.Column('status', sa.Enum('ENABLE', 'DISABLE', 'EXPIRED', 'PENDING', 'LOCKED', 'HIDDEN', name='statustypes'), nullable=False),
    sa.Column('invite_by', sa.Uuid(), nullable=False),
    sa.Column('invite_code', sa.Uuid(), nullable=False),
    sa.Column('notifications_enabled', sa.Boolean(), nullable=False),
    sa.Column('is_visible', sa.Boolean(), nullable=False),
    sa.Column('custom_title', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['invite_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['invite_code'], ['invite_codes.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('team_id', 'user_id', name='unique_team_user')
    )
    op.create_index(op.f('ix_team_user_join_id'), 'team_user_join', ['id'], unique=False)
    op.create_index(op.f('ix_team_user_join_team_id'), 'team_user_join', ['team_id'], unique=False)
    op.create_index(op.f('ix_team_user_join_user_id'), 'team_user_join', ['user_id'], unique=False)
    op.create_table('thread',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('query', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_thread_id'), 'thread', ['id'], unique=False)
    op.create_table('checkpoint_blobs',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('thread_id', sa.Uuid(), nullable=False),
    sa.Column('checkpoint_ns', sa.String(), server_default='', nullable=False),
    sa.Column('channel', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('version', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('blob', sa.LargeBinary(), nullable=True),
    sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'channel', 'version')
    )
    op.create_table('checkpoint_writes',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('thread_id', sa.Uuid(), nullable=False),
    sa.Column('checkpoint_ns', sa.String(), server_default='', nullable=False),
    sa.Column('checkpoint_id', sa.Uuid(), nullable=False),
    sa.Column('task_id', sa.Uuid(), nullable=False),
    sa.Column('idx', sa.Integer(), nullable=False),
    sa.Column('channel', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('blob', sa.LargeBinary(), nullable=False),
    sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx')
    )
    op.create_table('checkpoints',
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('thread_id', sa.Uuid(), nullable=False),
    sa.Column('checkpoint_ns', sa.String(), server_default='', nullable=False),
    sa.Column('checkpoint_id', sa.Uuid(), nullable=False),
    sa.Column('parent_checkpoint_id', sa.Uuid(), nullable=True),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('checkpoint', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_id', 'checkpoint_ns')
    )
    op.create_table('model',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('ai_model_name', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('provider_id', sa.Uuid(), nullable=False),
    sa.Column('categories', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('capabilities', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['provider_id'], ['modelprovider.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_id'), 'model', ['id'], unique=False)
    op.create_table('upload',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=True),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.Column('dataset_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.Boolean(), nullable=False),
    sa.Column('chunk_size', sa.Integer(), nullable=False),
    sa.Column('chunk_overlap', sa.Integer(), nullable=False),
    sa.Column('file_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('file_path', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('file_size', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_upload_id'), 'upload', ['id'], unique=False)
    op.create_table('embedding',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=True),
    sa.Column('document', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('upload_id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('team_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.ForeignKeyConstraint(['upload_id'], ['upload.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cmetadata_gin', 'embedding', ['cmetadata'], unique=False, postgresql_using='gin', postgresql_ops={'cmetadata': 'jsonb_path_ops'})
    op.create_index(op.f('ix_embedding_id'), 'embedding', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_embedding_id'), table_name='embedding')
    op.drop_index('ix_cmetadata_gin', table_name='embedding', postgresql_using='gin', postgresql_ops={'cmetadata': 'jsonb_path_ops'})
    op.drop_table('embedding')
    op.drop_index(op.f('ix_upload_id'), table_name='upload')
    op.drop_table('upload')
    op.drop_index(op.f('ix_model_id'), table_name='model')
    op.drop_table('model')
    op.drop_table('checkpoints')
    op.drop_table('checkpoint_writes')
    op.drop_table('checkpoint_blobs')
    op.drop_index(op.f('ix_thread_id'), table_name='thread')
    op.drop_table('thread')
    op.drop_index(op.f('ix_team_user_join_user_id'), table_name='team_user_join')
    op.drop_index(op.f('ix_team_user_join_team_id'), table_name='team_user_join')
    op.drop_index(op.f('ix_team_user_join_id'), table_name='team_user_join')
    op.drop_table('team_user_join')
    op.drop_index(op.f('ix_modelprovider_id'), table_name='modelprovider')
    op.drop_table('modelprovider')
    op.drop_index(op.f('ix_graph_parent'), table_name='graph')
    op.drop_index(op.f('ix_graph_id'), table_name='graph')
    op.drop_table('graph')
    op.drop_index(op.f('ix_dataset_name'), table_name='dataset')
    op.drop_index(op.f('ix_dataset_id'), table_name='dataset')
    op.drop_index('ix_dataset_cmetadata_gin', table_name='dataset', postgresql_using='gin', postgresql_ops={'cmetadata': 'jsonb_path_ops'})
    op.drop_table('dataset')
    op.drop_index(op.f('ix_apikey_id'), table_name='apikey')
    op.drop_table('apikey')
    op.drop_index(op.f('ix_team_id'), table_name='team')
    op.drop_table('team')
    op.drop_index(op.f('ix_user_phone'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_tenant_name'), table_name='tenant')
    op.drop_index(op.f('ix_tenant_id'), table_name='tenant')
    op.drop_table('tenant')
    op.drop_index(op.f('ix_dictionary_arguments_id'), table_name='dictionary_arguments')
    op.drop_table('dictionary_arguments')
    op.drop_index(op.f('ix_invite_codes_id'), table_name='invite_codes')
    op.drop_table('invite_codes')
    op.drop_index(op.f('ix_dictionaries_name'), table_name='dictionaries')
    op.drop_index(op.f('ix_dictionaries_id'), table_name='dictionaries')
    op.drop_table('dictionaries')
    # ### end Alembic commands ###
