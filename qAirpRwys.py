#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

global magnVari

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

def deciLati( tStr):
  # input NDDMMSSSS
  tDeci  = int( tStr[1:3] )
  tDeci += float (tStr[3:5]) /60 
  tDeci += float (tStr[5:]) / ( 3600 * 100 )
  if (tStr[0] == 'S') :
    tDeci *= -1
  return ( tDeci)

def deciLong( tStr):
  # WDDDMMSSSS
  tDeci  = int   (tStr[1:4] )
  tDeci += float (tStr[4:6]) / 60.0 
  tDeci += float (tStr[6:]) / ( 3600.0 * 100 )
  if (tStr[0] == 'W') :
    tDeci *= -1
  return ( tDeci)

def ft2Mtr ( tStr):
  # FF
  if ( tStr == '' ) :
    return( 0)
  else :  
    tDeci  = (int(tStr) * 12 * 0.0254)
    return ( tDeci)
    
def trueHdng( tStr):
  global magnVari
  tHdng = float(tStr[0:4]) / 10.0
  if  ( len(tStr) < 5 ):
    tHdng -= magnVari
  else:   
    if ( (tStr[4]) != 'T' ) :
      tHdng -= magnVari
  return(tHdng)
   
def get_magnVari() :
  global magnVari
  with dbConn.cursor() as cur:
    # query airport table for Mag Variation
    tQuery = "SELECT * FROM cycle2403.airport \
              WHERE airport_identifier='%s'" % airpId 
    cur.execute( tQuery)
    row = cur.fetchone()
    if ( cur.rowcount != 1 ) :
      print("Error, non-singleton Airport count: ", cur.rowcount)
    else : 
      tMagVar = float(row[14][1:]) / 10.0
      if ( row[14][0] != 'W' ):
        tMagVar *= -1
      magnVari = tMagVar 
      
def pairRwys( tRows) :
  rwysDone = []
  for aRow in tRows :
    # strip 'RW', add to rwysDone 
    tIden = aRow[6]
    rwysDone.append(tIden)
    idLast = tIden[len(tIden)-1]
    if (idLast.isalpha()) :
      idNumb = int(tIden[2:len(tIden)-1])
      idChar = idLast
    else :
      idNumb = int(tIden[2:])
      idChar = ''
    if (idNumb > 18 ) :  
      rcipNumb = idNumb - 18
    else:  
      rcipNumb = idNumb + 18
    rcipChar = ''  
    if (idChar == 'L') :
      rcipChar = 'R' 
    if (idChar == 'R') :
      rcipChar = 'L'
    rcipId = ( "RW%02i%s" % (rcipNumb, rcipChar))
    # Find rcip rwy in list 
    for aRow in tRows :
      # strip 'RW', add to rwysDone 
      thisId = aRow[6]
      if ( (not( thisId in rwysDone))  & (not( rcipId in rwysDone)) ):
        if ( thisId == rcipId ) :
          rwysDone.append(thisId)
          print( 'Rcip Match: ', tIden, thisId)
  

def get_rwys():
  """ Retrieve data from database runway table """
  global airpId, magnVari
  config  = load_config()
  #     
  with dbConn.cursor() as cur:
    # query runway table 
    tQuery = "SELECT * FROM cycle2403.runway \
              WHERE airport_identifier='%s'" % airpId 
    cur.execute( tQuery)
    #print("rowcount: ", cur.rowcount)
    row = cur.fetchone()

    while row is not None:
      tIden = row[6]
      mHdng = row[9]
      tHdng = trueHdng( mHdng)
      tLati = row[10]
      dLati = deciLati( tLati)
      tLong = row[11]
      dLong = deciLong( tLong)
      tDisp =       ( row[15])
      mDisp = ft2Mtr( row[15])
      tStop =       ( row[21])
      mStop = ft2Mtr( row[21])
      print( "Iden: %s  HdgT: %3.1f  dLati: %3.5f  dLong: %3.5f  mDisp: %4.1f  mStop: %4.1f" % \
        (tIden, tHdng, dLati, dLong, mDisp, mStop))
      row = cur.fetchone()
    cur.execute( tQuery)
    allRows = cur.fetchall()
    pairRwys( allRows)


if __name__ == '__main__':
  global magnVari
  normArgs(sys.argv[1:])
  magnVari = 15.00
  config  = load_config()
  try:
    dbConn = psycopg2.connect(**config)
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)
  get_magnVari()        
  get_rwys()        
