curl -X POST -d '{"current": "insufficient data", "alarm_id": "5f905ad6-c67a-4c6e-92bd-3fd179b5de42", "reason": "1 datapoints are unknown", "reason_data": {"count": 1, "most_recent": null, "type": "threshold", "disposition": "unknown"}, "previous": "ok"}' -s 'http://localhost:9999/v1/sla/alarming?status=alarm&source=ceilometer&contract_id=6c4b6667-f392-456a-8f12-bc473bf21f26'

