#!/bin/bash
docker build --tag ghcr.io/makidoll/toxlidge:latest --target toxlidge .
docker push ghcr.io/makidoll/toxlidge:latest
