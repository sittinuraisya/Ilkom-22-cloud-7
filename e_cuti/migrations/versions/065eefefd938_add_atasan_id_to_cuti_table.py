"""add atasan_id to cuti table

Revision ID: 065eefefd938
Revises: 716542f0c8c2
Create Date: 2025-04-14 19:02:29.384681

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '065eefefd938'
down_revision = '716542f0c8c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cuti', schema=None) as batch_op:
        batch_op.add_column(sa.Column('atasan_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'users', ['atasan_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cuti', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('atasan_id')

    # ### end Alembic commands ###
