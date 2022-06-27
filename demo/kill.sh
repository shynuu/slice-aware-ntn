#!/bin/bash

docker compose -f ../code/testbeds/saw-ntn/docker-compose.yaml down -v
docker compose -f ../code/testbeds/suaw-ntn/docker-compose.yaml down -v