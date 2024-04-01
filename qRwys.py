#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

def normArgs(argv):
  global airpId
# fallback values
  airpId = 'KAOH'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:", \
      ["airfId="] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ("-a", "--airpId"):
      airpId  = arg
  #
#

def get_locs():
  """ Retrieve data from the localizers table """
  global airpId
  config  = load_config()
  try:
    with psycopg2.connect(**config) as conn:
      with conn.cursor() as cur:
        cur.execute("""
          SELECT * FROM cycle2403.runway
          WHERE  airport_identifier=""" + "'" + str(airpId) + "'"
        )
        print("rowcount: ", cur.rowcount)
        row = cur.fetchone()

        while row is not None:
          print(row)
          row = cur.fetchone()

  except (Exception, psycopg2.DatabaseError) as error:
      print(error)

if __name__ == '__main__':
  normArgs(sys.argv[1:])
  get_locs()        
