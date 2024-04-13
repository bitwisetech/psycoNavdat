#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

def normArgs(argv):
  global airpId, vorId
# fallback values
  airpId = 'KAOH'
  vorId = 'PUT'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:i:", \
      ["airfId=", "id=" ] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ("-a", "--airpId"):
      airpId  = arg
    if   opt in ("-i", "--id"):
      vorId  = arg
  #
#

def get_vors():
  """ Retrieve data from the navaid table """
  global airpId, vorId
  config  = load_config()
  try:
    with psycopg2.connect(**config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM cycle2403.vhf_navaid \
         WHERE  vor_identifier='%s'" % vorId
        cur.execute(tQuery)
        print("rowcount: ", cur.rowcount)
        row = cur.fetchone()

        while row is not None:
          print(row)
          row = cur.fetchone()

  except (Exception, psycopg2.DatabaseError) as error:
      print(error)

if __name__ == '__main__':
  normArgs(sys.argv[1:])
  get_vors()        
