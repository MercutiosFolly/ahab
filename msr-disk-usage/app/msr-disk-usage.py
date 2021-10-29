#############################################################
# @file     msr-disk-usage.py
# @author   James Hind
# @date     07/25/21
# @ver      1.3
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
#   Rev 1.3 - 10/20/21 - JH - implement v2 paging (where applicable)
#
# @todo
#   - Paging implemented in v2 but I found a solution using v0 - retrieve from
#   header
#   - Collapse "get_*_size" into a single recursive
#   - Finish documentation
#   - Optimize functions. iteration takes a while
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
    def __init__(self, url, user, token, units, ca_path, debug, legacy, api_page_size):
        self.url        = url
        self.user       = user
        self.token      = token
        self.units      = units
        self.ca_path    = ca_path
        self.debug      = debug
        self.legacy     = legacy            # Used to enable pagination by using /v2/catalog/ on newer versions
        self.api_page_size = api_page_size  # Not implemented

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
    repo_size = 0
    tag_size_json_aggregate = []
    endpoint_link = "&pageSize=" + str(props.api_page_size) +"&pageStart="
    num_tags_processed = 0

    flag_all_tags_processed = False
    while not flag_all_tags_processed:
        # Get batch of tags in repo
        endpoint = "https://" + props.url + "/api/v0/repositories/" + repo + "/tags?count=true&includeManifests=false" + endpoint_link
        endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

        try:
            req = requests.get( endpoint, auth=(props.user, props.token),
                    headers=endpoint_headers, verify=props.ca_path )
        except:
            sys.exit( f"[Fatal] Unable to connect to MSR to retrieve repo data. Is your URL/IP valid?" )

        if req.status_code != 200:
            sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

        num_tags  = req.headers["X-Resource-Count"]
        if props.debug == True:
            print( f"{repo} Tag Count:\t {num_tags}", file=sys.stderr )
        tag_list_json = req.json()

        # For each tag -> get size data
        for tag in tag_list_json:
            tag_name = repo + "/tags/" + tag[ "name" ]
            tag_size_json = get_tag_size( tag_name, props )
            repo_size += tag_size_json[ "size" ]
            tag_size_json_aggregate.append( tag_size_json )
            num_tags_processed += 1

        # Follow link for paging
        if "x-next-page-start" in req.headers:
            endpoint_link = "&pageSize=" + str(props.api_page_size) +"&pageStart=" + req.headers["X-Next-Page-Start"]
        else:
            if num_tags_processed < int( num_tags ):
                print( f"[Warn] Potential discrepency in number of processed tags. It may be advantageous to rerun the program to verify results.", file=sys.stderr )
            flag_all_tags_processed = True

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
    ns_size = 0
    ns_size_json_aggregate = []

    if props.legacy == True: # Use api/v0 - forego paging
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
        for repo in repositories_api_list_json[ "repositories" ]:
            ns = repo[ "namespace" ]
            if ns not in ns_arr:
                ns_arr.append( repo[ "namespace" ] ) # track ns we already found
                ns_size_json = get_ns_size( ns, props )
                ns_size += ns_size_json[ "size" ]
                ns_size_json_aggregate.append( ns_size_json )

    else: # Use api/v2
        num_repos_processed = 0
        endpoint_link = "/v2/_catalog?n=" + str( props.api_page_size )
        while num_repos_processed < int( num_repos ):
            # Get/refresh v2 token
            # @TODO: implement refresh tokens
            endpoint = "https://" + props.url + "/auth/token?client_id=msr-disk-usage&grant_type=password&username=" + props.user + "&password=" + props.token + "&scope=registry:catalog:*"
            endpoint_headers = {'accept': 'application/json', 'content-type': 'application/json'}

            try:
                req = requests.post( endpoint, headers=endpoint_headers, verify=props.ca_path )
            except:
                sys.exit( f"[Fatal] Unable to connect to MSR to retrieve token (v2). Is your URL/IP valid?" )

            if req.status_code != 200:
                sys.exit( f"[Fatal] Failed to reach API endpoint at /auth/token: Status code {req.status_code}" )

            auth_payload = req.json()
            token_v2 = auth_payload["access_token"]

            # Request batch of repos
            endpoint = "https://" + props.url + endpoint_link
            endpoint_headers = {'Authorization': f'Bearer {token_v2}', 'accept': 'application/json', 'content-type': 'application/json'}

            try:
                req = requests.get( endpoint, headers=endpoint_headers, verify=props.ca_path )
            except:
                sys.exit( f"[Fatal] Unable to connect to MSR to retrieve repo data (v2). Is your URL/IP valid?" )

            if req.status_code != 200:
                sys.exit( f"[Fatal] Failed to reach API endpoint at {endpoint}: Status code {req.status_code}" )

            ns_api_list_json = []
            for x in req.json()[ "repositories" ]:
                ns_api_list_json.append( x.split("/")[0] )
                num_repos_processed += 1

            # Follow link for paging: https://docs.docker.com/registry/spec/api/#listing-repositories
            if req.links.get('next'):
                endpoint_link = req.links['next']['url']
            elif num_repos_processed < int( num_repos ):
                print( f"[Warn] Potential discrepency in number of processed repos. It may be advantageous to rerun the program to verify results.", file=sys.stderr )

            # For each namespace -> get size data
            for ns in ns_api_list_json:
                if ns not in ns_arr:
                    ns_arr.append( ns ) # track ns we already found
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

    # Input Handling
    def arg_positive( a_arg ):
        arg = int( a_arg )
        if arg <=0:
            raise argparse.ArgumentTypeError("Expecting positive integer")
        return arg

    parser = argparse.ArgumentParser(
        description='Calculate Namespace/Repo/tag footprint of MSR. Depending on the size of the MSR installation, this may take some time to execute',
        epilog='**All returned sizes are in MB unless otherwise specified' )
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
        help='User access token (or password) of MSR user. Example: password' )
    parser.add_argument(
        '-u',
        '--units',
        choices = ['b', 'kb', 'mb', 'gb'],
        default = 'mb',
        help='Units to represent size: b = bytes, kb = kilobytes, mb = megabytes (default), gb = bigabytes' )
    parser.add_argument(
        '-s',
        '--page-size',
        type=arg_positive,
        default = 10,
        help='Maximum page size for API requests.' )
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help=argparse.SUPPRESS )
    parser.add_argument(
        '-l',
        '--legacy',
        action='store_true',
        default=False,
        help='Use legacy mode for compatiblity. Forces use of v0 API calls only. Will likely adversely affect performance if MSR installation is very large.' )

    args = parser.parse_args()

    # Configure program properties
    props = Properties( args.url, args.username, args.token, args.units,
            msr_ca_path, args.debug, args.legacy, args.page_size )

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


