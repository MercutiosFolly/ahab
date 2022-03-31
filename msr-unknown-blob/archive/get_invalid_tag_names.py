#!/usr/local/bin/python3
import json


def open_file(name):
    f = open(name, "r")
    return f

def get_sha256sum_from_manifests(manifests_arr, invalid_blob_objects_arr):
    manifest_pk_arr = []
    for inv_blob_obj in invalid_blob_objects_arr:
        sha = inv_blob_obj["sha256sum"]
        for manifest in manifests_arr:
            pk = manifest["pk"]
            for layer in manifest["layers"]:
                digest = layer["digest"]
                if digest == sha:
                    if digest not in manifest_pk_arr:
                        manifest_pk_arr.append(pk)
                        print(f'Affected tag sha: {pk}')

    print(f'sha list: {manifest_pk_arr}')
    return manifest_pk_arr

def get_tag_names_from_sha256sum(tags_arr, manifest_pk_arr):
    tag_names_arr = []
    for pk in manifest_pk_arr:
        for tag in tags_arr:
            digestPK = tag["digestPK"]
            if digestPK == pk:
                tagPK = tag["pk"]
                if tagPK not in tag_names_arr:
                    tag_names_arr.append(tagPK)
                    print(f'Affected tag pk: {tagPK}')

    print(f'sha list: {tag_names_arr}')
    return tag_names_arr


if __name__ == '__main__':
    invalid_blobs_objects_filename = "invalid_blob_objects.json"
    invalid_blobs_objects_f_handler = open_file(invalid_blobs_objects_filename)
    invalid_blob_objects_arr = json.load(invalid_blobs_objects_f_handler)

    manifests_filename = "manifests.json"
    manifests_f_handler = open_file(manifests_filename)
    manifests_arr = json.load(manifests_f_handler)

    tags_filename = "tags.json"
    tags_f_handler = open_file(tags_filename)
    tags_arr = json.load(tags_f_handler)

    #image_names_arr = get_image_names_from_blob_links(blob_links_arr, invalid_blob_objects_arr)
    manifest_pk_arr = get_sha256sum_from_manifests(manifests_arr,
            invalid_blob_objects_arr)
    tag_names_arr = get_tag_names_from_sha256sum(tags_arr,
            manifest_pk_arr)
    invalid_tag_names_filename = "invalid_tag_names.json"
    with open(invalid_tag_names_filename, "w") as f:
        json.dump(tag_names_arr, f)

