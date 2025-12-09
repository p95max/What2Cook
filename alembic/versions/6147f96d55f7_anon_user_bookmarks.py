from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '6147f96d55f7'
down_revision = 'ca3137948eb4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = set(insp.get_table_names())

    if 'anon_user' not in tables:
        op.create_table(
            'anon_user',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
            sa.Column('last_seen', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        )

    if 'bookmarks' not in tables:
        op.create_table(
            'bookmarks',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('anon_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('recipe_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['anon_id'], ['anon_user.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        )
        op.create_unique_constraint('uq_bookmarks_anon_recipe', 'bookmarks', ['anon_id', 'recipe_id'])

def downgrade() -> None:
    try:
        op.drop_constraint('uq_bookmarks_anon_recipe', 'bookmarks', type_='unique')
    except Exception:
        pass
    try:
        op.drop_table('bookmarks')
    except Exception:
        pass
    try:
        op.drop_table('anon_user')
    except Exception:
        pass
