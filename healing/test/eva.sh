curl -X POST -d '{"data": {"target_resource": "ubuntu-Virtualbox"}}' -s http://localhost:9999/v1/handlers/evacuate/?source=custom -vv -H 'Content-Type: application/json'
