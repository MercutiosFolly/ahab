#!/bin/bash

if ! which jq &>/dev/null ; then
  echo "This script requires the jq tool for json processing:"
  echo "https://stedolan.github.io/jq/"
  exit
fi

echo -e "----------------- Configure -----------------\n"
read -p 'DTR FQDN (including port): ' DTR_FQDN
read -p 'Username: ' USER
read -sp 'Token (or password): ' TOKEN
JOBFILE="./joblist.json"

echo -e "\n\n----------------- Fetch Job List -----------------\n" 
curl -k -u ${USER}:${TOKEN} -X GET "https://${DTR_FQDN}/api/v0/jobs?action=scan_check&worker=any&running=f&start=0&limit=100" -H  "accept: application/json" -H  "Content-Type: application/json" 2>/dev/null > ${JOBFILE}

jq '[ .jobs[] | select( .status == "waiting" ) | { "id": .id, "type": .action, "status": .status } ]' ${JOBFILE}

echo -e "\n\n----------------- Cancel \"scan_check\" jobs in \"waiting\" status -----------------\n"
JOBLIST=$(cat joblist.json | jq '.jobs[] | select( .status == "waiting" ) | .id')

for JOB in ${JOBLIST[@]}; do
  JOB=$( echo $JOB | tr -d '"' )
  echo "Cancelling Jobs #: ${JOB}"
  curl -u ${USER}:${TOKEN} -X POST "https://${DTR_FQDN}/api/v0/jobs/${JOB}/cancel" -H  "accept: application/json" -H  "Content-Type: application/json"
  #curl -u ${USER}:${TOKEN} -X DELETE "https://${DTR_FQDN}/api/v0/jobs/${JOB}" -H  "accept: application/json" -H  "Content-Type: application/json"
done

echo -e "\n\n----------------- Fetch Job List -----------------\n"
curl -k -u ${USER}:${TOKEN} -X GET "https://${DTR_FQDN}/api/v0/jobs?action=scan_check&worker=any&running=f&start=0&limit=100" -H  "accept: application/json" -H  "Content-Type: application/json" 2>/dev/null > "$(basename -s .json ${JOBFILE})_finished.json"
