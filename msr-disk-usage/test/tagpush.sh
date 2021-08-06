#!/bin/bash
# @TODO This is not a real test suite, just a script for pushing repos to MSR
# NOTE: Need to create orgs whale1 - whale12 first and enable "create repo on push"
# NOTE: Need to trust CA, `docker login`, and `export DTR_FQDN` for this to work

#DTR_FQDN=xxx.xxx.xxx
docker pull nginx:latest
docker pull alpine:latest
docker pull busybox:latest
docker pull docker/ucp:3.2.1
docker pull docker/ucp:3.2.5
docker pull docker/ucp:3.2.7
docker pull docker/dtr:2.7.1
docker pull docker/dtr:2.7.5
docker pull docker/dtr:2.7.7

# @TODO Use API to create orgs/repos
for i in $(seq 1 12); do
  docker image tag nginx:latest     ${DTR_FQDN}:444/whale${i}/repo1:a
  docker image tag alpine:latest    ${DTR_FQDN}:444/whale${i}/repo1:b
  docker image tag busybox:latest   ${DTR_FQDN}:444/whale${i}/repo1:c
  docker image tag docker/ucp:3.2.1 ${DTR_FQDN}:444/whale${i}/repo2:1.0
  docker image tag docker/dtr:2.7.1 ${DTR_FQDN}:444/whale${i}/repo2:2.0
  echo ''
  docker image push ${DTR_FQDN}:444/whale${i}/repo1:a
  echo ''
  docker image push ${DTR_FQDN}:444/whale${i}/repo1:b
  echo ''
  docker image push ${DTR_FQDN}:444/whale${i}/repo1:c
  echo ''
  docker image push ${DTR_FQDN}:444/whale${i}/repo2:1.0
  echo ''
  docker image push ${DTR_FQDN}:444/whale${i}/repo2:2.0
  echo ''
done
