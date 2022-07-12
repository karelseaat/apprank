"""adding dev address

Revision ID: 2e614e6efefc
Revises: 09c552a6752c
Create Date: 2022-02-12 16:41:29.182468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e614e6efefc'
down_revision = '09c552a6752c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rankingapp', sa.Column('developeraddress', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('rankingapp', 'developeraddress')
    # ### end Alembic commands ###