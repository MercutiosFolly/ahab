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

    args = parser.parse_args()

    # Configure program properties
    props = Properties( args.url, args.username, args.token, args.units,
            msr_ca_path, args.debug, args.page_size )

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
        print( f"Total Repo Count:\t {num_repos}", file=sys.stderr )

    # Extract data 
    size_data_json = get_size_data( props )

    # Return data
    print( json.dumps( size_data_json ) )
    sys.exit()



