#!/usr/bin/env bash

OUTPUT=output
mkdir -p $OUTPUT

function die() {
    echo "ERROR:" "$@"
    exit 1
}

# Optional debug flags
if [ -z ${DEBUG+x} ]
then
    echo "DEBUG not set"
    FLAGS=""
else
    echo "DEBUG Set"
    FLAGS="--debug --verbose"
fi

# This is pretty tricky. In some cases, apparently, java refuses to close on a SIGPIPE, meaning that if
# the python process die, java will happily churn on.
# To avoit this, we get java to write to a pipe, and python to read from it. If any of the dies, we terminate.

echo "Making fifo for program to communicate"
mkfifo myfifo | die "Unable to create fifo"

echo "Starting java log-tracer"
java -jar log-tracer-1.6.jar -b $KAFKA_BROKER -p $KAFKA_PORT -t $KAFKA_TOPIC > myfifo &

echo "Starting python filter"
python3 filter-log.py --folder $OUTPUT $FLAGS < myfifo &

# To allow both program to start.
echo "Waiting for both programs to start"
sleep 5

echo "Waiting for one of the programs to stop/die"

wait -n || true
echo "One of the elements of the pipe stopped working. Shutting down in 5 seconds."
# Sleep a bit, to allow the other program to stop. If the java died, we can still get the nice zip file.
sleep 5
die "Done"

