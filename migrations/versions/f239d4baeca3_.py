"""empty message

Revision ID: f239d4baeca3
Revises: a80f5395d183
Create Date: 2016-03-12 14:50:06.880502

"""

# revision identifiers, used by Alembic.
revision = 'f239d4baeca3'
down_revision = 'a80f5395d183'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entry', sa.Column('wishlist', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('entry', 'wishlist')
    ### end Alembic commands ###
