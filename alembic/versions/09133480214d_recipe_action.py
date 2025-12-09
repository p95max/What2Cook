from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '09133480214d'
down_revision = '6147f96d55f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if 'recipe_action' not in tables:
        op.create_table(
            'recipe_action',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('anon_user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('recipe_id', sa.Integer(), nullable=False),
            sa.Column('action_type', sa.String(length=32), nullable=False),  # 'bookmark' | 'like' | etc
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['anon_user_id'], ['anon_user.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        )
        op.create_index(
            'ix_recipe_action_user_type_created_at',
            'recipe_action',
            ['anon_user_id', 'action_type', 'created_at']
        )
        op.create_unique_constraint(
            'uq_recipe_action_unique',
            'recipe_action',
            ['anon_user_id', 'recipe_id', 'action_type']
        )


def downgrade() -> None:
    try:
        op.drop_constraint('uq_recipe_action_unique', 'recipe_action', type_='unique')
    except Exception:
        pass
    try:
        op.drop_index('ix_recipe_action_user_type_created_at', table_name='recipe_action')
    except Exception:
        pass
    try:
        op.drop_table('recipe_action')
    except Exception:
        pass
