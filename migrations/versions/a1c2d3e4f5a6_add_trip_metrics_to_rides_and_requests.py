"""Add trip metrics: rides.distance_km, rides.duration_min, ride_requests.detour_min

Revision ID: a1c2d3e4f5a6
Revises: 5ef329471ff1
Create Date: 2026-11-15 21:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c2d3e4f5a6'
down_revision = '5ef329471ff1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('rides', schema=None) as batch_op:
        batch_op.add_column(sa.Column('distance_km', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('duration_min', sa.Float(), nullable=True))
        batch_op.create_check_constraint('chk_ride_distance_positive', 'distance_km IS NULL OR distance_km > 0')
        batch_op.create_check_constraint('chk_ride_duration_positive', 'duration_min IS NULL OR duration_min > 0')

    with op.batch_alter_table('ride_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('detour_min', sa.Float(), nullable=True))
        batch_op.create_check_constraint('chk_request_detour_nonnegative', 'detour_min IS NULL OR detour_min >= 0')


def downgrade():
    with op.batch_alter_table('ride_requests', schema=None) as batch_op:
        batch_op.drop_constraint('chk_request_detour_nonnegative', type_='check')
        batch_op.drop_column('detour_min')

    with op.batch_alter_table('rides', schema=None) as batch_op:
        batch_op.drop_constraint('chk_ride_duration_positive', type_='check')
        batch_op.drop_constraint('chk_ride_distance_positive', type_='check')
        batch_op.drop_column('duration_min')
        batch_op.drop_column('distance_km')
