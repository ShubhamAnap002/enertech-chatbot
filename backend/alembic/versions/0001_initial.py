"""Initial schema — create_all is also used at startup; this revision documents baseline."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables are managed via SQLAlchemy metadata.create_all in development.
    # Production should generate autogenerate diffs from models.
    pass


def downgrade() -> None:
    pass
