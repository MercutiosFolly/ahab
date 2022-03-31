import json


def open_file(name):
    f = open(name, "r")
    return f


def get_image_names_from_blob_links(blob_links_arr, invalid_blob_objects_arr):
    invalid_image_names_arr = []
    for inv_blob_obj in invalid_blob_objects_arr:
        sha = inv_blob_obj["sha256sum"]
        for blob_link in blob_links_arr:
            blob_link_digest = blob_link["digest"]
            if sha == blob_link_digest:
                namespace = blob_link["namespace"]
                repository = blob_link["repository"]
                image_name = namespace + "/" + repository
                if image_name not in invalid_image_names_arr:
                    invalid_image_names_arr.append(image_name)

    return invalid_image_names_arr


if __name__ == '__main__':
    invalid_blobs_objects_filename = "invalid_blob_objects.json"
    invalid_blobs_objects_f_handler = open_file(invalid_blobs_objects_filename)
    invalid_blob_objects_arr = json.load(invalid_blobs_objects_f_handler)

    blob_links_filename = "blob_links_test.json"
    blob_links_f_handler = open_file(blob_links_filename)
    blob_links_arr = json.load(blob_links_f_handler)

    image_names_arr = get_image_names_from_blob_links(blob_links_arr, invalid_blob_objects_arr)
    invalid_image_names_filename = "invalid_image_names.json"
    with open(invalid_image_names_filename, "w") as f:
        json.dump(image_names_arr, f)

