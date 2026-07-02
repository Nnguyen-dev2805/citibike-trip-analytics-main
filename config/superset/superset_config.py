import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-this-local-secret")
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:superset@superset-db:5432/superset"
WTF_CSRF_ENABLED = True
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}
