FROM apache/superset:3.1.3

USER root
RUN pip install --no-cache-dir trino==0.330.0 sqlalchemy-trino==0.5.0
USER superset
