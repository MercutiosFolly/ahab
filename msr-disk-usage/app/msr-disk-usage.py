#############################################################
# @file     msr-disk-usage.py
# @author   James Hind
# @date     07/25/21
# @ver      1.0
#
# @brief
#  Tool for calculating the backend storage  space usage of orgs/repos/tags 
#  for Mirantis Secure Registry. Size in MB
#
# @details
#   - Tested on MSR 2.9.0 - mileage may vary between versions as API changes
#     can and do occur
#
# @todo
#   - Check the format of inputs, not just number
#   - Collapse url, user, token -> access object
#   - It should be possible to collapse "get_*_size" into a single recursive
#   - Make "size" units adjustable
#   - Finish documentation
#   - containerize
#############################################################

import requests
import json
import sys

# Disable ssl warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#############################################################
# @fn get_tag_size
def get_tag_size( tag, url, user, token, ca ):
    tag_size_json = {}
    # Get tag reference data
    endpoint = "https://" + url + "/api/v0/repositories/" + tag
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    req = requests.get( endpoint, auth=(user, token), headers=endpoint_headers, verify=ca )
    if req.status_code != 200:
        sys.exit( f"Fatal: Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    tag_json = req.json()

    # Get tag size
    tag_size_json = { "tag": tag, "size": tag_json[0][ "manifest" ][ "size"]/1000000 }
    return tag_size_json

#############################################################
# @fn get_repo_size
def get_repo_size( repo, url, user, token, ca ):
    repo_size_json = {}
    # Get tags in repo
    endpoint = "https://" + url + "/api/v0/repositories/" + repo + "/tags?count=true&includeManifests=false"
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    req = requests.get( endpoint, auth=(user, token), headers=endpoint_headers, verify=ca )
    if req.status_code != 200:
        sys.exit( f"Fatal: Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    tag_num  = req.headers["X-Resource-Count"]
    tag_list_json = req.json()

    # For each tag -> get size data
    repo_size = 0
    tag_size_json_aggregate = {}
    for tag in tag_list_json:
        tag_name = repo + "/tags/" + tag[ "name" ]
        tag_size_json = get_tag_size( tag_name, url, user, token, ca )
        repo_size += tag_size_json[ "size" ]
        tag_size_json_aggregate[ tag_name ] = tag_size_json

    repo_size_json = { "repo": repo, "size": repo_size, "tags": [ tag_size_json_aggregate ] }
    return repo_size_json

#############################################################
# @fn get_ns_size
# @att 
#   See notes for \ref get_size_data()
def get_ns_size( ns, url, user, token, ca ):
    ns_size_json = {}
    # Get repos in namespace (API)
    endpoint = "https://" + url + "/api/v0/repositories/" + ns + "?count=true"
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    req = requests.get( endpoint, auth=(user, token), headers=endpoint_headers, verify=ca )
    if req.status_code != 200:
        sys.exit( f"Fatal: Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    repo_num  = req.headers["X-Resource-Count"]
    repo_list_json = req.json()

    # For each repo -> get size data
    ns_size = 0
    repo_size_json_aggregate = {}
    for repo in repo_list_json[ "repositories" ]:
        repo_name = repo[ "namespace" ] + "/" + repo[ "name" ]
        repo_size_json = get_repo_size( repo_name, url, user, token, ca )
        ns_size += repo_size_json[ "size" ]
        repo_size_json_aggregate[repo_name] = repo_size_json

    ns_size_json = { "namespace": ns, "size": ns_size, "repos": [ repo_size_json_aggregate ] }
    return ns_size_json

#############################################################
# @fn get_size_data
# @att 
#   the API has two end-points for accessing repos. One list all repos
#   across all namespaces, the other only lists repos in a particular namespace.
#   The list that gets passed to this function is the former, while the list
#   we work with in \ref get_ns_size is the latter. Do not be confused by the
#   similar "repo_list_json" naming
def get_size_data( repositories_api_list_json, url, user, token, ca ):
    size_data_json = {}
    ns_arr = []
    # For each namespace -> get size data
    ns_size = 0
    ns_size_json_aggregate = {}
    for repo in repositories_api_list_json[ "repositories" ]:
        ns = repo[ "namespace" ]
        if ns not in ns_arr:
            ns_arr.append( repo[ "namespace" ] ) # track ns we already found
            ns_size_json = get_ns_size( ns, url, user, token, ca )
            ns_size += ns_size_json[ "size" ]
            ns_size_json_aggregate[ ns ] = ns_size_json

    size_data_json = { "name": "total", "size": ns_size, "namespaces": [ ns_size_json_aggregate ] }
    return size_data_json

#############################################################
# @fn main
if __name__ == '__main__':
    # Variables
    msr_ca_file = "/tmp/msr_ca.pem"

    # Input Handling
    if len(sys.argv) != (3 + 1): # "+ 1" to account for sys.argv[0]
        sys.exit( print(f"Invalid Arguments. Usage:\n"
              f"\t{sys.argv[0]} url username token|password\n\n"
              f"\tWhere,\n"
              f"\t\turl      = url of MSR including port. Example: <ip>:<port>\n"
              f"\t\tusername = username of user to access MSR as. Example: admin\n"
              f"\t\ttoken    = user access token of MSR user\n"
              f"\t\tpassword = password of MSR user\n"
              f"\n"
              f"\t\t**All sizes in MB") )

    url   = sys.argv[1]
    user  = sys.argv[2]
    token = sys.argv[3]

    # Get MSR CA
    endpoint_ca = "https://" + url + "/ca"
    req = requests.get( endpoint_ca, verify=False )
    if req.status_code != 200:
        sys.exit( f"Fatal: Failed to reach API endpoint at {endpoint_ca}: Status code {req.status_code}" )

    msr_ca = req.text
    with open( msr_ca_file, "w" ) as f:
        f.write( msr_ca )

    # Obtain repo list
    endpoint_repos = "https://" + url + "/api/v0/repositories?count=true"
    endpoint_repos_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    req = requests.get( endpoint_repos, auth=(user, token), headers=endpoint_repos_headers, verify=msr_ca_file )
    if req.status_code != 200:
        sys.exit( f"Fatal: Failed to reach API endpoint at {endpoint_repos}: Status code {req.status_code}" )

    repo_num  = req.headers["X-Resource-Count"]
    repositories_api_list_json = req.json()

    # Extract data 
    size_data_json = get_size_data( repositories_api_list_json, url, user, token, msr_ca_file )

    # Return data
    print( json.dumps( size_data_json ) )
    sys.exit()


