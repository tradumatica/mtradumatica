"""Translator share_key col

Revision ID: 3de0e5f811d2
Revises: 
Create Date: 2020-06-03 12:15:14.713761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3de0e5f811d2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'translator_from_bitext', ['share_key'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'translator_from_bitext', type_='unique')
    # ### end Alembic commands ###
