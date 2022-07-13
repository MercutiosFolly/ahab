#!/bin/bash

REPLICA_ID=$(docker ps --filter name=dtr-rethink --format '{{ .Names }}' | cut -d'-' -f3)

# Get Specific Repo
#echo "r.db('dtr2').table('tags').filter( {'pk': 'whale/repo1:c'} )" | docker run --rm -i --net dtr-ol -e DTR_REPLICA_ID=${REPLICA_ID} -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > dtr2-tags-whale-repo1-c.json
#echo "r.db('dtr2').table('manifests').filter({ 'repository': 'whale/repo1'} )" | docker run --rm -i --net dtr-ol -e DTR_REPLICA_ID=${REPLICA_ID} -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > dtr2-manifests-repo1.json

# Get All Repos
echo "r.db('dtr2').table('tags')" | docker run --rm -i --net dtr-ol -e DTR_REPLICA_ID=${REPLICA_ID} -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > dtr2-tags.json
echo "r.db('dtr2').table('manifests')" | docker run --rm -i --net dtr-ol -e DTR_REPLICA_ID=${REPLICA_ID} -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > dtr2-manifests.json

# Required
echo "r.db('dtr2').table('blob_links')" | docker run --rm -i --net dtr-ol -e DTR_REPLICA_ID=${REPLICA_ID} -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > dtr2-blob_links.json
echo "r.db('dtr2').table('blobs')" | docker run --rm -i --net dtr-ol -e DTR_REPLICA_ID=${REPLICA_ID} -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > dtr2-blobs.json
