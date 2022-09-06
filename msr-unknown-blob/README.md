# msr-unknown-blob

## Overview

An issue that is occasionally observed in image registries is the "unknown blob" issue.
Each image has it's own "manifest" which is essentially a record of the blobs that make up
the image. This error is the registry indicating that it is unable to locate one or more of
the blobs in its backend storage.

When faced with this issue a common inquiry is, "what tags are affected by this?" This tools
aims to help answer this question.

**ATTENTION**
This tool is provided as-is with no guarantees. It is recommended that you have backups
of your metadata and backend storage prior to utilizing this tool.

## Usage

In order to identify what tags are affected, we need to gather a file stat of the backend
storage and fetch some data from the rethinkdb instance. Consequently, we need to run this
tool in the cluster in order to mount the necessary volumes and access the dtr-ol network.

```
docker image pull jhind/msr-unknown-blob:x.x

REPLICA_ID=$(docker ps --filter name=dtr-rethink --format '{{ .Names }}' | cut -d'-' -f3)

docker run -it --rm \
  --name msr-unknown-blob \
  --net dtr-ol \
  --volume dtr-ca-${REPLICA_ID}:/ca:ro \
  --volume dtr-registry-${REPLICA_ID}:/registry:ro \
  jhind/msr-unknown-blob:1.0 ${REPLICA_ID} > affected_tags.out.txt
```

## Sample Output

```
Affected Tags:

whale1/repo1:a
whale11/repo1:a
whale10/repo1:a
whale3/repo1:a
whale6/repo1:a
whale2/repo1:a
whale5/repo1:a
whale7/repo1:a
whale12/repo1:a
whale8/repo1:a
whale9/repo1:a
whale4/repo1:a
```

