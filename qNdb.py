#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

def normArgs(argv):
  global dbIniFId, cyclTabl, ndbId, wantHelp
# fallback values
  dbIniFId = "a424db.ini"
  cyclTabl = "cycle2403.ndb_navaid"
  ndbId = 'ADG'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "d:hi:", \
      ["database=", help, "id=" ] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if opt in ("-d", "--database"):
      if ( arg == "x" ) :
        dbIniFId = "x810db.ini"
        cyclTabl = "cyclexp810.ndb_navaid"
      if ( arg == "a" ) :
        dbIniFId = "a424db.ini"
        cyclTabl = "cycle2403.ndb_navaid"
    if opt in ('-h', "--help"):
      wantHelp = 1
    if   opt in ("-i", "--id"):
      ndbId  = arg
  #
#

def get_ndbs():
  """ Retrieve data from the navaid table """
  global  dbIniFId, cyclTabl, ndbId
  config  = load_config(filename=dbIniFId)
  try:
    with psycopg2.connect(**config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE ndb_identifier=\'%s\' " \
        % (cyclTabl, ndbId)
        cur.execute(tQuery)
        print("rowcount: ", cur.rowcount)
        row = cur.fetchone()

        while row is not None:
          print(row)
          row = cur.fetchone()

  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
#

def showHelp() :
  progName = sys.argv[0]
  print("  ")
  print(" %s : Query NDB entries in ARINC424 or Flightgear database " % progName )
  print("  ")
  print("Prerequ: ")
  print("  Install PyARINC424 and build the ARINC242     postsegrsql database  ")
  print("  Install PyNavdat   and build Flightgear xp810 postsegrsql database  ")
  print("  ")
  print("Arguments:")
  print("  -d --database= 'a' | 'x' Query ARINC424 (default) | Flightgear X810 ")
  print("  -i --id=       Ident ( default ADG ) of NDB")
  print("  ")
#

if __name__ == '__main__':
  normArgs(sys.argv[1:])
  #
  if (wantHelp > 0 ) :
    showHelp()
  print( "Query %s in %s database: " % ( ndbId, dbIniFId[0:4]))
  get_ndbs()        
