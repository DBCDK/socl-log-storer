# SOCL log storer

Small utility to filter json log lines from a kafka topic, and store them in files for later analysis.

## Testinput

You can create a testinput like this:

```
log-tracer -b kafka-p01 -p 9093 -t prod_socl_cisterne > testinput.jsonl
```
## Command lines
log-tracer -b kafka-p01 -p 9093 -t prod_socl_cisterne | python3 src/filter-log.py

## Example output
```
{
    "timestamp": "2019-11-25T12:40:03.748+00:00",
    "version": "1",
    "message": "[20190701_504_stored_shard5_replica_n17]  webapp=/solr path=/select params={q=scanphrase.default:\"per\\+kongsted\"&qt=/select&fl=scanphrase.default&appId=cisterne-suggestion-service&rows=5&wt=javabin&version=2} hits=1 status=0 QTime=5",
    "logger": "org.apache.solr.core.SolrCore.Request",
    "thread": "qtp1922464006-7334764",
    "level": "INFO",
    "level_value": 20000,
    "mdc": {
        "core": "x:20190701_504_stored_shard5_replica_n17",
        "replica": "r:core_node18",
        "node_name": "n:socl-p09.dbc.dk:18003_solr",
        "collection": "c:20190701_504_stored",
        "shard": "s:shard5"
    },
    "app": "solr8",
    "webapp": "/solr",
    "path": "/select",
    "params": "{q=scanphrase.default:\"per\\+kongsted\"&qt=/select&fl=scanphrase.default&appId=cisterne-suggestion-service&rows=5&wt=javabin&version=2}",
    "params_values": {
        "q": "scanphrase.default:\"per\\+kongsted\"",
        "qt": "/select",
        "fl": [
            "scanphrase.default"
        ],
        "appId": "cisterne-suggestion-service",
        "rows": "5",
        "wt": "javabin",
        "version": "2"
    },
    "hits": "1",
    "status": "0",
    "QTime": "5",
    "appId": "cisterne-suggestion-service",
    "calltime": "2019-11-25T12:40:03.743000+00:00"
}
```
Lines 'timestamp' to 'app' are original log data.
Lines 'webapp' to 'calltime' added by extracted from message original data, parsing and adding extra data

