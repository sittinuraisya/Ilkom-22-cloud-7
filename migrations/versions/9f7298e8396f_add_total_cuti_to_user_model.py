"""Add total_cuti to User model

Revision ID: 9f7298e8396f
Revises: eb790f217952
Create Date: 2025-04-13 18:41:22.221565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f7298e8396f'
down_revision = 'eb790f217952'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total_cuti', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('total_cuti')

    # ### end Alembic commands ###
