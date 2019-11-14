# SOCL log storer

Small utility to filter json log lines from a kafka topic, and store them in files for later analysis.

## Testinput

You can create a testinput like this:

```
log-tracer -b kafka-p01 -p 9093 -t prod_socl_cisterne > testinput.jsonl
```
