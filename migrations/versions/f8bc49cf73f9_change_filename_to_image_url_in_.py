"""Change filename to image_url in ItemImage model

Revision ID: f8bc49cf73f9
Revises: 0eac6e84a4e7
Create Date: 2025-03-14 03:26:10.242020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8bc49cf73f9'
down_revision = '0eac6e84a4e7'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column
    op.add_column('item_image', sa.Column('image_url', sa.String(length=512), nullable=True))
    
    # Update data - convert filename to image_url
    op.execute("UPDATE item_image SET image_url = '/static/uploads/' || filename")
    
    # Make image_url not nullable
    op.alter_column('item_image', 'image_url', nullable=False)
    
    # Drop the old column
    op.drop_column('item_image', 'filename')


def downgrade():
    # Add the old column
    op.add_column('item_image', sa.Column('filename', sa.VARCHAR(length=255), nullable=True))
    
    # Extract filename from image_url
    op.execute("UPDATE item_image SET filename = SUBSTR(image_url, INSTR(image_url, '/uploads/') + 9)")
    
    # Make filename not nullable
    op.alter_column('item_image', 'filename', nullable=False)
    
    # Drop the new column
    op.drop_column('item_image', 'image_url')
