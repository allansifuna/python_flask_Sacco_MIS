"""empty message

Revision ID: 5fa239a6a766
Revises: f8d0c8ef2352
Create Date: 2022-10-31 09:50:43.979924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fa239a6a766'
down_revision = 'f8d0c8ef2352'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ticket', sa.Column('date_created', sa.DateTime(), nullable=True))
    op.add_column('ticket_message', sa.Column('date_created', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ticket_message', 'date_created')
    op.drop_column('ticket', 'date_created')
    # ### end Alembic commands ###
