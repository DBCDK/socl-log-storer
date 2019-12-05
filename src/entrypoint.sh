#!/usr/bin/env bash

OUTPUT=output
mkdir -p $OUTPUT

# Optional debug flags
if [ -z ${DEBUG+x} ]
then
    echo "DEBUG not set"
    FLAGS=""
else
    echo "DEBUG Set"
    FLAGS="--debug --verbose"
fi

java -jar log-tracer-1.6.jar -b $KAFKA_BROKER -p $KAFKA_PORT -t $KAFKA_TOPIC | python3 filter-log.py --folder $OUTPUT $FLAGS