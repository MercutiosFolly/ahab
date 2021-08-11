#############################################################
# @file     msr-disk-usage.py
# @author   James Hind
# @date     07/25/21
# @ver      1.1
#
# @brief
#  Tool for calculating the backend storage  space usage of orgs/repos/tags 
#  for Mirantis Secure Registry. Size in MB
#
# @details
#   - Tested on MSR 2.9.0 - mileage may vary between versions as API changes
#     can and do occur.
#   - This program does not account for shared/cross-mounted layers so results
#     may differ from actual on-disk size
#
#   Rev 1.0 - 07/25/21 - JH - initial release
#   Rev 1.1 - 08/01/21 - JH - Add input handling, fix json formatting, migrate
#       to property class, add adjustable size query
#   Rev 1.2 - 08/02/21 - JH - Generalize to accomodate paging (paging
#       unavailable - pending feature request
#
# @todo
#   - Handle paging. Current solution is to catch resource count
#     and set pageSize=count, but this is not quite as robust for extremely large
#     systems. Pending feature request to expose the namespaceAccountID or
#     allow paging off of a different value.
#   - Collapse "get_*_size" into a single recursive
#   - Finish documentation
#############################################################

import requests
import json
import argparse
import sys

# Disable ssl warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#############################################################
# @class properties
class Properties:
    def __init__(self, url, user, token, units, ca_path, debug, api_page_size):
        self.url        = url
        self.user       = user
        self.token      = token
        self.units      = units
        self.ca_path    = ca_path
        self.debug      = debug
        self.api_page_size = api_page_size

#############################################################
# @fn get_tag_size
def get_tag_size( tag, props ):
    tag_size_json = {}
    # Get tag reference data
    endpoint = "https://" + props.url + "/api/v0/repositories/" + tag
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    try:
        req = requests.get( endpoint, auth=(props.user, props.token),
                headers=endpoint_headers, verify=props.ca_path )
    except:
        sys.exit( f"[Fatal] Unable to connect to MSR to retrieve tag data. Is your URL/IP valid?" )

    if req.status_code != 200:
        sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    tag_json = req.json()

    # Get tag size
    factor = 1
    if props.units == 'b':
        factor = 1
    elif props.units == 'kb':
        factor = 1000
    elif props.units == 'mb':
        factor = 1000000
    elif props.units == 'gb':
        factor = 1000000000
    else:
        print( f"[Warn] No size units provided, using MB", file=sys.stderr )
        factor = 1000000

    tag_size_json = { "id": tag, "type": "tag", "size": tag_json[0]["manifest"]["size"]/factor }
    return tag_size_json

#############################################################
# @fn get_repo_size
def get_repo_size( repo, props ):
    repo_size_json = {}
    # Get tags in repo
    endpoint = "https://" + props.url + "/api/v0/repositories/" + repo + "/tags?count=true&includeManifests=false"
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    try:
        req = requests.get( endpoint, auth=(props.user, props.token),
                headers=endpoint_headers, verify=props.ca_path )
    except:
        sys.exit( f"[Fatal] Unable to connect to MSR to retrieve repo data. Is your URL/IP valid?" )

    if req.status_code != 200:
        sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    tag_num  = req.headers["X-Resource-Count"]
    if props.debug == True:
        print( f"{repo} Tag Count:\t {tag_num}", file=sys.stderr )
    tag_list_json = req.json()

    # For each tag -> get size data
    repo_size = 0
    tag_size_json_aggregate = []
    for tag in tag_list_json:
        tag_name = repo + "/tags/" + tag[ "name" ]
        tag_size_json = get_tag_size( tag_name, props )
        repo_size += tag_size_json[ "size" ]
        tag_size_json_aggregate.append( tag_size_json )

    repo_size_json = { "id": repo, "type": "repo", "size": repo_size, "members": tag_size_json_aggregate }
    return repo_size_json

#############################################################
# @fn get_ns_size
# @att 
#   See notes for \ref get_size_data()
def get_ns_size( ns, props ):
    ns_size_json = {}
    # Get repos in namespace (API)
    endpoint = "https://" + props.url + "/api/v0/repositories/" + ns + "?count=true"
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    try:
        req = requests.get( endpoint, auth=(props.user, props.token),
                headers=endpoint_headers, verify=props.ca_path )
    except:
        sys.exit( f"[Fatal] Unable to connect to MSR to retrieve namespace data. Is your URL/IP valid?" )

    if req.status_code != 200:
        sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    repo_num  = req.headers["X-Resource-Count"]
    if props.debug == True:
        print( f"{ns} Repo Count:\t {repo_num}", file=sys.stderr )
    repo_list_json = req.json()

    # For each repo -> get size data
    ns_size = 0
    repo_size_json_aggregate = []
    for repo in repo_list_json[ "repositories" ]:
        repo_name = repo[ "namespace" ] + "/" + repo[ "name" ]
        repo_size_json = get_repo_size( repo_name, props )
        ns_size += repo_size_json[ "size" ]
        repo_size_json_aggregate.append( repo_size_json )

    ns_size_json = { "id": ns, "type": "namespace", "size": ns_size, "members": repo_size_json_aggregate }
    return ns_size_json

#############################################################
# @fn get_size_data
# @att 
#   the API has two end-points for accessing repos. One list all repos
#   across all namespaces, the other only lists repos in a particular namespace.
#   The list that gets passed to this function is the former, while the list
#   we work with in \ref get_ns_size is the latter. Do not be confused by the
#   similar "repo_list_json" naming
def get_size_data( num_repos, props ):
    size_data_json = {}
    ns_arr = []

    endpoint = "https://" + props.url + "/api/v0/repositories/?pageSize=" + num_repos + "&count=true"
    endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    try:
        req = requests.get( endpoint, auth=(props.user, props.token),
                headers=endpoint_headers, verify=props.ca_path )
    except:
        sys.exit( f"[Fatal] Unable to connect to MSR to retrieve repo data. Is your URL/IP valid?" )

    if req.status_code != 200:
        sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

    repo_num  = req.headers["X-Resource-Count"]
    repositories_api_list_json = req.json()

    # For each namespace -> get size data
    ns_size = 0
    ns_size_json_aggregate = []
    for repo in repositories_api_list_json[ "repositories" ]:
        ns = repo[ "namespace" ]
        if ns not in ns_arr:
            ns_arr.append( repo[ "namespace" ] ) # track ns we already found
            ns_size_json = get_ns_size( ns, props )
            ns_size += ns_size_json[ "size" ]
            ns_size_json_aggregate.append( ns_size_json )

    size_data_json = { "id": "total", "type": "aggregate", "size": ns_size, "members": ns_size_json_aggregate }
    return size_data_json

#############################################################
# @fn main
if __name__ == '__main__':
    # Variables
    msr_ca_path = "/tmp/msr_ca.pem"
    api_page_size = 10 #Tune the number of entries returned in a single API call

    # Input Handling
    parser = argparse.ArgumentParser(
        description='Calculate Namespace/Repo/tag footprint of MSR.',
        epilog='**All returned sizes are in MB.' )
    parser.add_argument(
        'url',
        metavar='url',
        help='Url of MSR including port. Example: 123.123.123.123:444' )
    parser.add_argument(
        'username',
        metavar='username',
        help='Username to use when accessing MSR. Example: admin' )
    parser.add_argument(
        'token',
        metavar='token',
        help='User access token (or password) of MSR user' )
    parser.add_argument(
        '-u',
        '--units',
        choices = ['b', 'kb', 'mb', 'gb'],
        default = 'mb',
        help='Units to represent size: b = bytes, kb = kilobytes, mb = megabytes (default), gb = bigabytes' )
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help='Enable debug mode' )

    args = parser.parse_args()

    # Configure program properties
    props = Properties( args.url, args.username, args.token, args.units,
            msr_ca_path, args.debug, api_page_size )

    # Get MSR CA
    endpoint_ca = "https://" + props.url + "/ca"
    try:
        req = requests.get( endpoint_ca, verify=False )
    except:
        sys.exit( f"[Fatal] Unable to connect to MSR to retrieve CA. Is your URL/IP valid?" )

    if req.status_code != 200:
        sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint_ca}: Status code {req.status_code}" )

    msr_ca = req.text
    with open( props.ca_path, "w" ) as f:
        f.write( msr_ca )

    # Obtain repo count
    endpoint_repos = "https://" + props.url + "/api/v0/repositories?pageSize=1&count=true"
    endpoint_repos_headers = {'accept': 'application/json', 'content-type': 'application/json'}

    try:
        req = requests.get( endpoint_repos, auth=(props.user, props.token),
                headers=endpoint_repos_headers, verify=props.ca_path )
    except:
        sys.exit( f"[Fatal] Unable to connect to MSR to retrieve count. Is your URL/IP valid?" )

    if req.status_code != 200:
        sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint_repos}: Status code {req.status_code}" )

    num_repos  = req.headers["X-Resource-Count"]
    if props.debug == True:
        print( f"total Repo Count:\t {num_repos}", file=sys.stderr )

    # Extract data 
    size_data_json = get_size_data( num_repos, props )

    # Return data
    print( json.dumps( size_data_json ) )
    sys.exit()


