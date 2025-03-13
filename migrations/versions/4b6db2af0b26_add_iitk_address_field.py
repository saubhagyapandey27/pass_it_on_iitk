"""Add IITK address field

Revision ID: 4b6db2af0b26
Revises: b607077bb015
Create Date: 2024-03-12 17:34:46.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b6db2af0b26'
down_revision = 'b607077bb015'
branch_labels = None
depends_on = None


def upgrade():
    # Add column with a default value
    op.add_column('user', sa.Column('iitk_address', sa.String(length=20), nullable=False, server_default='Not Set'))


def downgrade():
    op.drop_column('user', 'iitk_address')
