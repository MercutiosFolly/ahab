#############################################################
# @file     __main__.py
# @author   James Hind
# @date     12/01/21
# @ver      1.3
#
# @brief
#
# @details
#
#   Rev 1.0 - 12/01/21 - JH - initial release
#
# @todo
#   - This needs to accomodate windows as well
#   - Consider making msinfo a class instead of function
#     - Can add properties as members -> more coherent than 
#       external def or passing around
#############################################################

import argparse
import sys
import . as ahab_du

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

