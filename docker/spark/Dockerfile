FROM apache/spark:3.5.1

USER root
WORKDIR /opt/project

ARG DELTA_VERSION=3.2.0
ARG HADOOP_AWS_VERSION=3.3.4
ARG AWS_SDK_BUNDLE_VERSION=1.12.262
ARG ANTLR_VERSION=4.9.3
ARG WILDFLY_OPENSSL_VERSION=1.0.7.Final

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN python3 - <<'PY'
from pathlib import Path
from urllib.request import urlretrieve

jars = {
    "delta-spark_2.12-3.2.0.jar": "https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.0/delta-spark_2.12-3.2.0.jar",
    "delta-storage-3.2.0.jar": "https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.0/delta-storage-3.2.0.jar",
    "hadoop-aws-3.3.4.jar": "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar",
    "aws-java-sdk-bundle-1.12.262.jar": "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar",
    "antlr4-runtime-4.9.3.jar": "https://repo1.maven.org/maven2/org/antlr/antlr4-runtime/4.9.3/antlr4-runtime-4.9.3.jar",
    "wildfly-openssl-1.0.7.Final.jar": "https://repo1.maven.org/maven2/org/wildfly/openssl/wildfly-openssl/1.0.7.Final/wildfly-openssl-1.0.7.Final.jar",
}

target = Path("/opt/spark/jars")
target.mkdir(parents=True, exist_ok=True)
for filename, url in jars.items():
    destination = target / filename
    if not destination.exists():
        print(f"Downloading {filename}")
        urlretrieve(url, destination)
PY

ENV PYTHONPATH=/opt/project
ENV SPARK_HOME=/opt/spark

CMD ["bash"]
