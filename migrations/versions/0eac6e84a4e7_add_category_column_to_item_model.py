"""Add category column to Item model

Revision ID: 0eac6e84a4e7
Revises: 4b6db2af0b26
Create Date: 2025-03-13 16:18:28.944270

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0eac6e84a4e7'
down_revision = '4b6db2af0b26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=False, server_default='other'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('item', schema=None) as batch_op:
        batch_op.drop_column('category')

    # ### end Alembic commands ###
