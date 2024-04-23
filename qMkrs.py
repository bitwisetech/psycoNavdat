#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

def normArgs(argv):
  global aCycle, airpId, dbIniFId, cyclTabl, vorId, wantHelp
# fallback values
  dbIniFId = 'a424db.ini'
  aCycle   = 'cycle2403'
  aTable   = 'localizer_marker'
  xCycle   = 'cyclexp810'
  xTable   = 'ndat_om'
  cyclTabl = ("%s.%s" % (aCycle, aTable))
  airpId = 'KATL'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:d:ht;", \
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
        cyclTabl = ("%s.%s" % (xCycle, xTable))
      if ( arg == "a" ) :
        dbIniFId = "a424db.ini"
        cyclTabl = ("%s.%s" % (aCycle, aTable))
    if opt in ('-h', "--help"):
      wantHelp = 1
  #
#

def get_mkrs():
  """ Retrieve data from the localizers table """
  global aCycle, airpId, dbIniFId, cyclTabl, vorId
  config  = load_config(filename=dbIniFId)
  if (aCycle in cyclTabl) :
    try:
      with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
          tQuery = "SELECT * FROM %s WHERE Airport_Identifier=\'%s\' " \
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
  print(" %s : Query OMI Marker entries in ARINC424 or Flightgear database " % progName )
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
  get_mkrs()        
