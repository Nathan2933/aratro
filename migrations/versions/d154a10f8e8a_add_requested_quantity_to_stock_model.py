"""Add requested_quantity to Stock model

Revision ID: d154a10f8e8a
Revises: 
Create Date: 2024-03-19 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd154a10f8e8a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary table with the new schema
    op.create_table('_stock_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('requested_quantity', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('farmer_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['farmer_id'], ['farmer.id'], ),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data from the old table to the new table
    op.execute("""
        INSERT INTO _stock_new (
            id, type, quantity, requested_quantity, status, farmer_id, warehouse_id,
            created_at, updated_at
        )
        SELECT 
            id, type, quantity, quantity as requested_quantity,
            COALESCE(status, 'pending') as status,
            farmer_id, warehouse_id,
            CURRENT_TIMESTAMP as created_at,
            CURRENT_TIMESTAMP as updated_at
        FROM stock
    """)
    
    # Drop the old table
    op.drop_table('stock')
    
    # Rename the new table to the original name
    op.rename_table('_stock_new', 'stock')


def downgrade():
    # Create a temporary table with the old schema
    op.create_table('_stock_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('farmer_id', sa.Integer()),
        sa.Column('warehouse_id', sa.Integer()),
        sa.Column('date_added', sa.DateTime()),
        sa.Column('status', sa.String(length=20)),
        sa.ForeignKeyConstraint(['farmer_id'], ['farmer.id'], ),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back to the old schema
    op.execute("""
        INSERT INTO _stock_old (
            id, type, quantity, farmer_id, warehouse_id, date_added, status
        )
        SELECT 
            id, type, quantity, farmer_id, warehouse_id, created_at, status
        FROM stock
    """)
    
    # Drop the new table
    op.drop_table('stock')
    
    # Rename the old table back to the original name
    op.rename_table('_stock_old', 'stock')
