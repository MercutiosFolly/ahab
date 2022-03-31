# AHAB

## Overview
The purpose of this repo is to serve as a place to maintain my more consolidated MKE/MSR/MCR tooling. Items
will be added as I convert my more loosely connected scripts into actual tools consumable by others.

As for the name. I'm hunting whales.

## Tools

### msr-disk-usage
#### Overview
  This tool is to assist people with analyzing the footprint of the registry images to reduce size and bloat.

#### Usage
  1. You can either pull the image from docker hub or build the image yourself using the provided Dockerfile

  `docker pull jhind/msr-disk-usage`

  2. To utilize the image, run the following command. Note that, depending on the size of MSR, it may take some time 
  for it to finish processing.

  ```bash
  export MSR_IP=<ip>
  export MSR_PORT=<port>
  export USER=<user>
  export TOKEN=<token>
  docker run -it --rm jhind/msr-disk-usage ${MSR_IP}:${MSR_PORT} ${USER} ${TOKEN} > data.json

  # For further information:
  docker run -it --rm jhind/msr-disk-usage --help
  ```

  3. Once the data is obtained, one can use any json parsing tools to filter through the information. Here are
  some examples using [jq](https://stedolan.github.io/jq/)

  ```bash
  # Display total size only
  cat data.json | jq ' { "total": .size} '

  # Display namespace size only - sorted in descending order
  cat data.json | jq '[ .members[] | { "namespace": .id, "size": .size }] | sort_by(.size) | reverse'

  # Display tag size only - sorted in descending order
  cat data.json | jq '[ .members[].members[] | { "namespace": .id, "size": .size }] | sort_by(.size) | reverse'

  # Display all info for specific namespace. 
  # Edit NAMESPACE to appropriate value: myorg
  cat data.json | jq '[ .members[] | select( .id == "NAMESPACE") ]'

  # Display only repo size for specific namespace
  # Edit NAMESPACE to appropriate value: myorg
  cat data.json | jq '[ .members[] | select( .id == "NAMESPACE") | .members[] | { "repo": .id, "size": .size} ] | sort_by(.size) | reverse'

  # Display tag size for specific repo
  # Edit NAMESPACE to appropriate value: myorg
  # Edit REPO to appropriate value: myorg/repo
  cat data.json | jq '[ .members[] | select( .id == "NAMESPACE") | .members[] | select( .id == "REPO" ) | .members[] | { "repo": .id, "size": .size} ] | sort_by(.size) | reverse'
  ```

#### Sample Output

```bash
$> docker run -it --rm jhind/msr-disk-usage:1.2 18.221.171.117:444 admin dockeradmin | jq
{
  "id": "total",
  "type": "aggregate",
  "size": 1302.261948,
  "members": [
    {
      "id": "whale9",
      "type": "namespace",
      "size": 108.521829,
      "members": [
        {
          "id": "whale9/repo1",
          "type": "repo",
          "size": 57.325534000000005,
          "members": [
            {
              "id": "whale9/repo1/tags/c",
              "type": "tag",
              "size": 0.766607
            },
            {
              "id": "whale9/repo1/tags/b",
              "type": "tag",
              "size": 2.813006
            },
            {
              "id": "whale9/repo1/tags/a",
              "type": "tag",
              "size": 53.745921
            }
          ]
        },
        {
          "id": "whale9/repo2",
          "type": "repo",
          "size": 51.196295,
          "members": [
            {
              "id": "whale9/repo2/tags/2.0",
              "type": "tag",
              "size": 31.53133
            },
            {
              "id": "whale9/repo2/tags/1.0",
              "type": "tag",
              "size": 19.664965
            }
          ]
        }
      ]
    },
```

### msr-unknown-blob

### mke-config
#### Overview

This tool provides a wrapper for adjusting various configuration settings in MKE (via the API). Note that the config options
it supports will exapand as needed so functionality may be limited initially.


