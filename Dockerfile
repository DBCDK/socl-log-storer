
FROM docker.dbc.dk/dbc-python3

LABEL KAFKA_BROKER="Kafka Broker. E.g. kafka-p01 (REQUIRED)"
LABEL KAFKA_PORT="Kafka port. E.g. 9093 (REQUIRED)"
LABEL KAFKA_TOPIC="Kafka topic to stream log output through filter. E.g. prod_socl_cisterne (REQUIRED)"

RUN apt-install dumb-init jdk8-dbc procps

ADD http://mavenrepo.dbc.dk/content/repositories/releases/dk/dbc/kafka/log-tracer/1.6/log-tracer-1.6.jar log-tracer-1.6.jar
COPY src/filter-log.py src/entrypoint.sh /

ENTRYPOINT [ "/usr/bin/dumb-init", "--", "./entrypoint.sh" ]