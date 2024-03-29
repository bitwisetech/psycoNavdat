#!/usr/bin/env python
import psycopg2
from config import load_config

def get_locs():
  """ Retrieve data from the localizers table """
  config  = load_config()
  try:
    with psycopg2.connect(**config) as conn:
      with conn.cursor() as cur:
        #cur.execute("SELECT airport_identifier FROM cycle2403.localizer ")
        cur.execute("""
          SELECT * FROM cycle2403.localizer
          WHERE  airport_identifier='KAOH' 
        """)
        print("rowcount: ", cur.rowcount)
        row = cur.fetchone()

        while row is not None:
          print(row)
          row = cur.fetchone()

  except (Exception, psycopg2.DatabaseError) as error:
      print(error)

if __name__ == '__main__':
  get_locs()        
