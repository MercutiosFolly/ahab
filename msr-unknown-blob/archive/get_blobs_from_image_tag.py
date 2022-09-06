#!/usr/local/bin/python3
#############################################################
# @file     get_blobs_from_image_tag.py
# @author   James Hind
# @date     06/06/21
# @ver      1.0
#
# @brief
#   1. Collect the requisite rethinkdb data: `rethink_image_dump.sh`
#   2. Run this script from the same directory as all of the resulting files
#   3. Script will consume the tag info and parse it down to the associate blob IDs
#
#############################################################
import json
import sys

def open_file(name):
    f = open(name, "r")
    return f

def get_tag_digest_pk(tag_json):
    tag_digest_pk = tag_json[0]['digestPK']
    print(f"Tag digestPK:\n{tag_digest_pk}")
    return tag_digest_pk

def get_manifest_layers(tag_digest_pk, manifest_json):
    manifest_layers_digest_arr = []
    for manifest_obj in manifest_json:
        if tag_digest_pk == manifest_obj["pk"]:
            for layer_obj in manifest_obj["layers"]:
                manifest_layers_digest_arr.append(layer_obj["digest"])
    print(f"{manifest_layers_digest_arr}")
    print(f"tag layer count:\t{len(manifest_layers_digest_arr)}")
    return manifest_layers_digest_arr

def get_blob_ids(manifest_layers_digest_arr, blobs_json):
    blob_id_arr = []
    for manifest_layer_digest_obj in manifest_layers_digest_arr:
        for blob_obj in blobs_json:
            if manifest_layer_digest_obj == blob_obj["sha256sum"]:
                blob_id_arr.append(blob_obj["id"])

    print(f"{blob_id_arr}")
    print(f"Blob ID count:\t{len(blob_id_arr)}")
    return blob_id_arr

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Invalid Arguments. Usage:\n\t{sys.argv[0]} repo image")
        sys.exit()

    repo = sys.argv[1]
    image = sys.argv[2]

    tag_filename        = f"{repo}_{image}_tag_dump.json"
    manifest_filename   = f"{repo}_{image}_manifest_dump.json"
    blob_links_filename = f"{repo}_{image}_blob-links_dump.json"
    blobs_filename      = f"{repo}_{image}_blobs_dump.json"

    tag_file        = open_file(tag_filename)
    manifest_file   = open_file(manifest_filename)
    blob_links_file = open_file(blob_links_filename)
    blobs_file      = open_file(blobs_filename)

    tag_json        = json.load(tag_file)
    manifest_json   = json.load(manifest_file)
    blob_links_json = json.load(blob_links_file)
    blobs_json      = json.load(blobs_file)

    tag_digest_pk = get_tag_digest_pk(tag_json)
    manifest_layers_digest_arr = get_manifest_layers(tag_digest_pk,
            manifest_json )
    blob_id_arr = get_blob_ids(manifest_layers_digest_arr, blobs_json)

    output_filename = f"{repo}_{image}_blob_ids.json"
    with open(output_filename, "w") as f:
        json.dump(blob_id_arr, f)

