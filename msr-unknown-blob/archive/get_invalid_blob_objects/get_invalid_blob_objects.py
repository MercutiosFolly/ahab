import json


def open_file(name):
    f = open(name, "r")
    return f


def get_invalid_blob_ids(file):
    lines = file.readlines()
    count = 0
    invalid_blob_ids_arr = []
    for line in lines:
        split_line = line.split()
        blob_status = split_line[-1] # either EXISTS or MISSING
        if blob_status == "MISSING":
            count += 1
            blob_path = split_line[-2]
            split_blob_path = blob_path.split("/")
            blob_id_path = split_blob_path[-2]
            blob_id_path_split = blob_id_path.split(",")
            invalid_blob_id = blob_id_path_split[-1]
            invalid_blob_ids_arr.append(invalid_blob_id)

    print(len(invalid_blob_ids_arr))
    return invalid_blob_ids_arr


def get_invalid_blob_objects(all_blobs_objects, invalid_blob_ids_arr):
    invalid_blob_objects = []
    for inv_blob_id in invalid_blob_ids_arr:
        for blob_obj in all_blobs_objects:
            if inv_blob_id == blob_obj["id"]:
                invalid_blob_objects.append(blob_obj)

    print("len:", len(invalid_blob_objects))
    return invalid_blob_objects


if __name__ == '__main__':
    # blob_links_filename = ""
    # blob_links_f_handler = open_file(blob_links_filename)
    #
    # blobs_filename = ""
    # read_manifest(manifest_filename, sha_arr)

    prev_script_output_filename = "blobsout.txt"
    prev_output_f_handler = open_file(prev_script_output_filename)
    invalid_blob_ids_arr = get_invalid_blob_ids(prev_output_f_handler)

    all_blob_objects_filename = "dtr2-blobs.json"
    all_blobs_f_handler = open_file(all_blob_objects_filename)
    all_blobs_objects_arr = json.load(all_blobs_f_handler)
    invalid_blob_objects_arr = get_invalid_blob_objects(all_blobs_objects_arr, invalid_blob_ids_arr)
    invalid_blob_objects_filename = "invalid_blob_objects.json"
    with open(invalid_blob_objects_filename, "w") as f:
        json.dump(invalid_blob_objects_arr, f)
