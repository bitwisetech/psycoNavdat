#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

def normArgs(argv):
  global airpId, dbIniFId, cyclTabl, vorId, wantHelp
# fallback values
  dbIniFId = "a424db.ini"
  cyclTabl = "cycle2403.localizer"
  airpId = 'KATL'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:d:h", \
      ["airpId=", "database="] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ("-a", "--airpId"):
      airpId  = arg
    if   opt in ("-d", "--database"):
      if ( arg == "x" ) :
        dbIniFId = "x810db.ini"
        cyclTabl = "cyclexp810.localizer"
      if ( arg == "a" ) :
        dbIniFId = "a424db.ini"
        cyclTabl = "cycle2403.localizer"
    if opt in ('-h', "--help"):
      wantHelp = 1
  #
#

def get_locs():
  """ Retrieve data from the localizers table """
  global airpId, dbIniFId, cyclTabl, vorId
  config  = load_config(filename=dbIniFId)
  try:
    with psycopg2.connect(**config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE airport_identifier=\'%s\' " \
        % (cyclTabl, airpId)
        cur.execute(tQuery)
        print("rowcount: ", cur.rowcount)
        row = cur.fetchone()

        while row is not None:
          print(row)
          row = cur.fetchone()

  except (Exception, psycopg2.DatabaseError) as error:
      print(error)

def showHelp() :
  progName = sys.argv[0]
  print("  ")
  print(" %s : Query LOC entries in ARINC424 or Flightgear database " % progName )
  print("  ")
  print("Prerequ: ")
  print("  Install PyARINC424 and build the ARINC242     postsegrsql database  ")
  print("  Install PyNavdat   and build Flightgear xp810 postsegrsql database  ")
  print("  ")
  print("Arguments:")
  print("  -d --database= 'a' | 'x' Query ARINC424 (default) | Flightgear X810 ")
  print("  -a --airpId=       Ident ( default KATL ) of Airport for all LOCs")
  print("  ")
#

if __name__ == '__main__':
  normArgs(sys.argv[1:])
  #
  if (wantHelp > 0 ) :
    showHelp()
  print( "Query %s in %s database: " % ( airpId, dbIniFId[0:4]))
  get_locs()        
