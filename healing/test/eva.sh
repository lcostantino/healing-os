curl -X POST -d '{"data": {"resource_id": "ubuntu-Virtualbox"}}' -s http://localhost:9999/v1/handlers/evacuate/?source=custom -vv -H 'Content-Type: application/json'
