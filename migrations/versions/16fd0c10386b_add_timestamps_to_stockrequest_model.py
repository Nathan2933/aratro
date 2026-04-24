"""Add timestamps to StockRequest model

Revision ID: 16fd0c10386b
Revises: d154a10f8e8a
Create Date: 2025-03-04 00:04:34.144521

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '16fd0c10386b'
down_revision = 'd154a10f8e8a'
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary table with the new schema
    op.create_table('_stock_request_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_id', sa.Integer(), nullable=False),
        sa.Column('to_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('request_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['from_id'], ['farmer.id']),
        sa.ForeignKeyConstraint(['to_id'], ['warehouse.id']),
        sa.ForeignKeyConstraint(['stock_id'], ['stock.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data from the old table to the new table
    op.execute("""
        INSERT INTO _stock_request_new (
            id, from_id, to_id, stock_id, request_date, status,
            created_at, updated_at
        )
        SELECT 
            id, from_id, to_id, stock_id, request_date, status,
            CURRENT_TIMESTAMP as created_at,
            CURRENT_TIMESTAMP as updated_at
        FROM stock_request
    """)
    
    # Drop the old table
    op.drop_table('stock_request')
    
    # Rename the new table to the original name
    op.rename_table('_stock_request_new', 'stock_request')


def downgrade():
    # Create a temporary table with the old schema
    op.create_table('_stock_request_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_id', sa.Integer(), nullable=False),
        sa.Column('to_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('request_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['from_id'], ['farmer.id']),
        sa.ForeignKeyConstraint(['to_id'], ['warehouse.id']),
        sa.ForeignKeyConstraint(['stock_id'], ['stock.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back to the old schema
    op.execute("""
        INSERT INTO _stock_request_old (
            id, from_id, to_id, stock_id, request_date, status
        )
        SELECT 
            id, from_id, to_id, stock_id, request_date, status
        FROM stock_request
    """)
    
    # Drop the new table
    op.drop_table('stock_request')
    
    # Rename the old table back to the original name
    op.rename_table('_stock_request_old', 'stock_request')
