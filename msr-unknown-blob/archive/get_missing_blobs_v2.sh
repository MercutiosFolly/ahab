#!/bin/bash

if [ -z "$1" ]
  then
    echo "No argument supplied, expecting path to blobs"
        exit 1
fi

REPLICA_ID=$(docker ps -lf name='^/dtr-rethinkdb-.{12}$' --format '{{.Names}}' | cut -d- -f3)
echo "r.db('dtr2').table('blobs').pluck('id')" | docker run -e DTR_REPLICA_ID=$REPLICA_ID -i --rm --net dtr-ol -v dtr-ca-$REPLICA_ID:/ca dockerhubenterprise/rethinkcli:v2.2.0-ni non-interactive > blobs.json
Blobs=(`sed -r -e 's/\]|\[//g' -e 's/\{"id":"([^"]+)"\},?/\1 /g' blobs.json`)

BasePath=$1/docker/registry/v2/blobs/id
for i in "${Blobs[@]}"
do
    filepath=$BasePath/${i:0:2}/$i/data
    if [ ! -s "$filepath" ]; then
        echo -e "${filepath} MISSING"
    else
        echo -e "${filepath} EXISTS"
    fi
done
