#############################################################
# @file     msr-unknown-blob.py
# @author   James Hind
# @date     09/01/21
# @ver      1.0
#
# @brief
#  Tool for analyzing consistency of MSR backend storage with RethinkDB
#  metadata
#
# @details
#   - Tested on MSR X.X.X - mileage may vary between versions as API changes
#     can and do occur.
#
#   Rev 1.0 - 09/01/21 - JH - initial release
#
#   - In order to do a consistency check, we need a few pieces of information
#       1. a stat map from mounted backend storage filesystem (can mount docker
#       volume to achieve)
#       2. Rethink table dumps: blobs, blob_links, tags (potentially more if we
#       want to expand returned information)
#     These two things cannot be obtained through the API so we are left with
#     deploying a local image similar to rethinkcli. Therefore, usage will
#     resemble the following:
#
#       docker run -e DTR_REPLICA_ID=$REPLICA_ID -i --rm --net
#       dtr-ol -v dtr-ca-$REPLICA_ID:/ca -v dtr-registry-nfs-$REPLICA_ID
#       jhind/msr-unknown-blob:1.0
#
#       and we will scrape the rethink tables (potentially uing rethinkcli as
#       base) Then do a hit/miss against the mounted dtr-registry volume. From
#       here we can identify the specific tags that are needed. 

#       Alternatively, can create an image that runs the scrape and spits out a
#       tar file which can be consumed by another tool for further analysis.
#       Minimum is provide flags for this functionality, 1 tool is better than
#       2 for usability purposes
#
# @attention
#   - The reql python driver does not support mutual TLS - which is required to
#     communicate with MSR rethink. This support may exist in JS, but I dislike
#     working in javascript. Alternatively, I can patch the library to allow it
#     but this is time and effort. Given this, we are just going to gather the
#     data manually, then use this to process them.
#
# @todo
#############################################################

import json
import argparse
import sys
import rethinkdb as r

#############################################################
# @class properties
class BlobAnalyzer:
    # Private Vars
    replica_id  = ""
    url         = ""
    port        = 28015
    ca          = "/ca/rethink/ca.pem"
    key         = "/ca/rethink-client/key.pem"
    cert        = "/ca/rethink-client/cert.pem"
    debug       = False

    # Constructor
    def __init__( self, replica_id, debug ):
        self.replica_id = replica_id
        self.debug      = debug
        self.url        = "dtr-rethinkdb-" + self.replica_id + ".dtr-ol"

    #############################################################
    # @fn 
    def get_missing_blobs( self ):
        connection = ""
        try:
            connection = r.connect( host = self.url, port = self.port, ssl = { 'ca': self.ca, 'key': self.key, 'cert': self.cert } )
        except:
            print( "[ERROR] Unable to connect to DB" )

        return True

    #############################################################
    # @fn 
    def get_rethink_tables( self ):
        return True

    #############################################################
    # @fn 
    def get_invalid_blob_abjects( self ):
        return True

    #############################################################
    # @fn 
    def get_invalid_tag_names( self ):
        return True

    #############################################################
    # @fn 
    def execute( self ):
        self.get_missing_blobs()
        self.get_rethink_tables()
        self.get_invalid_blob_abjects()
        self.get_invalid_tag_names()
        return True

#############################################################
# @fn main
if __name__ == '__main__':
    # Variables

    # Input Handling
    parser = argparse.ArgumentParser(
        description='Identifies MSR tags which are affected by "unknown blob".' )
    parser.add_argument(
        'replica_id',
        metavar='replica_id',
        help='Replica ID of rethink instance to connect to.' )
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help='Enable debug mode' )

    args = parser.parse_args()

    # Configure program properties
    analyzer = BlobAnalyzer( args.replica_id, args.debug )

    # Execute
    analyzer.execute()

    # Return data
    #print( json.dumps( invalid_tag_list ) )
    sys.exit()


