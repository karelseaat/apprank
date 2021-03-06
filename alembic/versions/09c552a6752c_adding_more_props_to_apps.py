"""adding more props to apps

Revision ID: 09c552a6752c
Revises: 033f0139ec8f
Create Date: 2022-02-11 16:25:12.959024

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09c552a6752c'
down_revision = '033f0139ec8f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rankingapp', sa.Column('textlen', sa.Integer(), nullable=True))
    op.add_column('rankingapp', sa.Column('adds', sa.Boolean(), nullable=True))
    op.add_column('rankingapp', sa.Column('movie', sa.Boolean(), nullable=True))
    op.add_column('rankingapp', sa.Column('inapppurchases', sa.Boolean(), nullable=True))
    op.add_column('rankingapp', sa.Column('developerwebsite', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('rankingapp', 'developerwebsite')
    op.drop_column('rankingapp', 'inapppurchases')
    op.drop_column('rankingapp', 'movie')
    op.drop_column('rankingapp', 'adds')
    op.drop_column('rankingapp', 'textlen')
    # ### end Alembic commands ###
