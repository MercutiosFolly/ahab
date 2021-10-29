#!/bin/bash
# @TODO This is not a real test, just a rough script for pushing repos to MSR
# NOTE: Need to enable "create repo on push"
# NOTE: Need to trust MSR CA for  `docker login`

# @TODO Add option to skip this
# @TODO Make it enable "create repo on push" instead of manually setting it
echo -e "-----------------Configure-----------------\n"
DTR_FQDN=xxx.xxx.xxx
read -p 'DTR FQDN (including port): ' DTR_FQDN
read -p 'UCP FQDN (including port): ' UCP_FQDN
read -p 'UCP username: ' UCP_USER
read -sp 'UCP password: ' UCP_PASSWORD

echo -e "\n\n-----------------MSR Login-----------------\n"
docker login ${DTR_FQDN}

echo -e "\n\n-----------------Create Orgs-----------------\n"
curl -k -u ${UCP_USER}:${UCP_PASSWORD} -X POST "https://${UCP_FQDN}/accounts/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"isOrg\": true,  \"name\": \"whale\"}"

for i in $(seq 1 12); do
  curl -k -u ${UCP_USER}:${UCP_PASSWORD} -X POST "https://${UCP_FQDN}/accounts/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"isOrg\": true,  \"name\": \"whale${i}\"}"
done

echo -e "\n\n-----------------Pull Images-----------------\n"
docker pull nginx:latest
docker pull alpine:latest
docker pull busybox:latest
docker pull docker/ucp:3.2.1
docker pull docker/ucp:3.2.5
docker pull docker/ucp:3.2.7
docker pull docker/dtr:2.7.1
docker pull docker/dtr:2.7.5
docker pull docker/dtr:2.7.7

echo -e "\n\n-----------------Tag & Push Images-----------------\n"
for i in $(seq 1 12); do
  docker image tag nginx:latest     ${DTR_FQDN}/whale${i}/repo1:a
  docker image tag alpine:latest    ${DTR_FQDN}/whale${i}/repo1:b
  docker image tag busybox:latest   ${DTR_FQDN}/whale${i}/repo1:c
  docker image tag docker/ucp:3.2.1 ${DTR_FQDN}/whale${i}/repo2:1.0
  docker image tag docker/dtr:2.7.1 ${DTR_FQDN}/whale${i}/repo2:2.0
  echo ''
  docker image push ${DTR_FQDN}/whale${i}/repo1:a
  echo ''
  docker image push ${DTR_FQDN}/whale${i}/repo1:b
  echo ''
  docker image push ${DTR_FQDN}/whale${i}/repo1:c
  echo ''
  docker image push ${DTR_FQDN}/whale${i}/repo2:1.0
  echo ''
  docker image push ${DTR_FQDN}/whale${i}/repo2:2.0
  echo ''
done
