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
#
#   Rev 1.0 - 09/01/21 - JH - Prelim
#   Rev 2.0 - 08/15/22 - JH - initial release
#
#   - Tested on MSR 2.9.X - mileage may vary between versions as API changes
#     can and do occur.
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
#       dtr-ol -v dtr-ca-$REPLICA_ID:/ca -v dtr-registry-nfs-$REPLICA_ID:/registry
#       jhind/msr-unknown-blob:1.0
#
#       and we will scrape the rethink tables (potentially uing rethinkcli as
#       base) Then do a hit/miss against the mounted dtr-registry volume. From
#       here we can identify the specific tags that are needed.
#
#       Alternatively, can create an image that runs the scrape and spits out a
#       tar file which can be consumed by another tool for further analysis.
#       Minimum is provide flags for this functionality, 1 tool is better than
#       2 for usability purposes
#
# @attention
#   - The reql python driver does not support mutual TLS - which is required to
#     communicate with MSR rethink. Therefore, I have forked the project and
#     made the necessary changes
#
# @todo
#   - This could be cleaned up. Instead of housing all of the process
#     variables in the class, its probably clearer if we pass them through the run()
#     sub functions
#############################################################

import sys, os
sys.path.append(os.path.join(sys.path[0],'third_party','rethinkdb_python'))

import json
import argparse
from rethinkdb import r

#############################################################
# @brief Input handler
def process_inputs():
    # Input Handling
    parser = argparse.ArgumentParser(
        description='Identifies MSR tags which are affected by "unknown blob".'
        )
    parser.add_argument(
        'replica_id',
        metavar='replica_id',
        help='Replica ID of rethink instance to connect to.'
        )
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help='Enable debug mode'
        )

    return parser.parse_args()

#############################################################
# @class BlobAnalyzer
class BlobAnalyzer:
    # Configuration Vars
    replica_id      = ""
    url             = ""
    port            = 28015
    ca              = "/ca/rethink/cert.pem"
    key             = "/ca/rethink-client/key.pem"
    cert            = "/ca/rethink-client/cert.pem"
    blob_storage    = "/registry/docker/registry/v2/blobs/id"

    db              = "dtr2"
    blobs_table     = "blobs"
    blob_links_table= "blob_links"
    tags_table      = "tags"
    manifests_table = "manifests"
    debug           = False

    # Rethink Data
    conn            = ""
    blobs           = {}
    blob_links      = {}
    tags            = {}
    manifests       = {}

    # Process Data
    blobs_stat      = {} # A dict containing the status of every blob
    blobs_missing   = [] # Collection of missing blob objects
    affected_tags   = [] # Array of tags affected by missing blobs

    # Constructor
    def __init__( self, replica_id, debug ):
        self.replica_id = replica_id
        self.debug      = debug
        self.url        = "dtr-rethinkdb-" + self.replica_id + ".dtr-ol"
        try:
            self.conn = r.connect(
                    db = self.db,
                    host = self.url,
                    port = self.port,
                    ssl = { 'ca_certs': self.ca, 'key': self.key, 'cert': self.cert }
                    )
        except Exception as e:
            print( f"[ERROR] Unable to connect to DB: {e}" )
            raise


    #############################################################
    # @fn
    def get_missing_blobs( self ):
        blob_ids = r.table( self.blobs_table ).pluck( 'id' ).run( self.conn )

        for blob_id in blob_ids:
            blob_file = self.blob_storage.rstrip("/") + "/" + blob_id['id'][:2] + "/" + blob_id['id'] + "/data"
            if os.path.isfile( blob_file ):
                self.blobs_stat[ blob_id['id'] ] = False
            else:
                self.blobs_stat[ blob_id['id'] ] = True

        if self.debug:
            with open( './00_blobs_stat.out', 'w' ) as file:
                for key, val in self.blobs_stat.items():
                    file.write( f'{key}\t{val}\n' )

        return True

    #############################################################
    # @fn
    def get_rethink_tables( self ):
        self.blobs = list(r.table( self.blobs_table ).run( self.conn ))
        self.blob_links = list(r.table( self.blob_links_table ).run( self.conn ))
        self.tags = list(r.table( self.tags_table ).run( self.conn ))
        self.manifests = list(r.table( self.manifests_table ).run( self.conn ))

        if self.debug:
            with open( './01_blobs.out.json', 'w' ) as file:
                file.write( str(self.blobs) )
            with open( './01_blob_links.out.json', 'w' ) as file:
                file.write( str(self.blob_links) )
            with open( './01_tags.out.json', 'w' ) as file:
                file.write( str(self.tags) )
            with open( './01_manifests.out.json', 'w' ) as file:
                file.write( str(self.manifests) )

        return True

    #############################################################
    # @fn
    def get_invalid_blob_abjects( self ):
        for blob_id, is_missing in self.blobs_stat.items():
            if is_missing:
                for blob in self.blobs:
                    if blob['id'] == blob_id:
                        self.blobs_missing.append( blob )
        if self.debug:
            with open( './02_blobs_missing.out.json', 'w' ) as file:
                file.write( str(self.blobs_missing) )

        return True

    #############################################################
    # @fn
    def get_invalid_tag_names( self ):
        # Collect the 'pk's of the manifests which reference a missing blob
        manifest_pk_arr = []
        for blob in self.blobs_missing:
            sha = blob['sha256sum']
            for manifest in self.manifests:
                pk = manifest['pk']
                for layer in manifest['layers']:
                    digest = layer['digest']
                    if digest == sha:
                        if digest not in manifest_pk_arr:
                            manifest_pk_arr.append(pk)

        if self.debug:
            with open( './03_affected_tag_sha.out.json', 'w' ) as file:
                file.write( str(manifest_pk_arr) )

        # Translate the manifests to tag names
        for pk in manifest_pk_arr:
            for tag in self.tags:
                digestPK = tag['digestPK']
                if digestPK == pk:
                    tagPK = tag['pk']
                    if tagPK not in self.affected_tags:
                        self.affected_tags.append( tagPK )

        if self.debug:
            with open( './04_affected_tag_pks.out.json', 'w' ) as file:
                file.write( str(self.affected_tags) )

        return True

    #############################################################
    # @fn
    def run( self ):
        self.get_missing_blobs()
        self.get_rethink_tables()
        self.get_invalid_blob_abjects()
        self.get_invalid_tag_names()

        print( f'Affected Tags:\n' )
        for pk in self.affected_tags:
            print( f'{pk}' )

        invalid_tag_names_filename = "invalid_tag_names.json"
        with open(invalid_tag_names_filename, "w") as f:
            json.dump(self.affected_tags, f)

        return True

#############################################################
# @fn main
def main() -> int:
    # Handle inputs
    args = process_inputs()

    # Configure program properties
    analyzer = BlobAnalyzer( args.replica_id, args.debug )

    # Execute
    analyzer.run()

    return 0

#############################################################
if __name__ == '__main__':
    # Return data
    sys.exit( main() )

