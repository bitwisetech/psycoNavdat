#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config
from lxml import etree


def normArgs(argv):
  global airpId, magnVari, outpDirp
# fallback values
  airpId   = 'KAOH'
  outpDirp = '/comm/fpln/cifp/Airports'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:d:", \
      ["airfId=", "outpDirp"] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ("-a", "--airpId"):
      airpId  = arg
    if   opt in ("-d", "--outpDirp"):
      outpDirp  = arg
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

def outpRway ( tRow) :
  global xPropl, xRway, xThrs, xIden, xHdng, xLati, xLong, xDisp, xStop
  tIden = tRow[6]
  mHdng = tRow[9]
  tHdng = trueHdng( mHdng)
  tLati = tRow[10]
  dLati = deciLati( tLati)
  tLong = tRow[11]
  dLong = deciLong( tLong)
  tDisp =       ( tRow[15])
  mDisp = ft2Mtr( tRow[15])
  tStop =       ( tRow[21])
  mStop = ft2Mtr( tRow[21])
  xThrs = etree.SubElement( xRway, "threshold")
  xIden = etree.SubElement( xThrs, "rwy")
  xIden.text = str( tIden )
  xHdng = etree.SubElement( xThrs, "hdg-deg")
  xHdng.text = str( tHdng )
  xLati = etree.SubElement( xThrs, "lat")
  xLati.text = str("%3.5f" % dLati )
  xLong = etree.SubElement( xThrs, "lon")
  xLong.text = str( "%3.5f" % dLong )
  xDisp = etree.SubElement( xThrs, "displ-m")
  xDisp.text = str( "%3.2f" % mDisp )
  xStop = etree.SubElement( xThrs, "stopw-m")
  xStop.text = str( "%3.2f" % mStop )
  print( "Iden: %s  HdgT: %3.1f  dLati: %3.5f  dLong: %3.5f  mDisp: %4.1f  mStop: %4.1f" % \
    (tIden, tHdng, dLati, dLong, mDisp, mStop))

def mill_thresholds():
  """ Retrieve data from database runway table """
  global airpId, magnVari, outpDirp
  global xPropl, xRway, xThrs, xIden, xHdng, xLati, xLong, xDisp, xStop
  rwysDone = []
  config   = load_config()
  xPropl = etree.Element("PropertyList")
  #
  with dbConn.cursor() as cur:
    # query runway table
    tQuery = "SELECT * FROM cycle2403.runway \
              WHERE airport_identifier='%s'" % airpId
    cur.execute( tQuery)
    allRows = cur.fetchall()
  for aRow in allRows :
    thisIcao = aRow[3]
    thisId   = aRow[6]
    if (not( thisId in rwysDone)) :
      print( '<runway>')
      xRway = etree.SubElement(xPropl, "runway")
      outpRway( aRow)
      rwysDone.append(thisId)
      idLast = thisId[len(thisId)-1]
      if (idLast.isalpha()) :
        idNumb = int(thisId[2:len(thisId)-1])
        idChar = idLast
      else :
        idNumb = int(thisId[2:])
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
      for tRow in allRows :
        # strip 'RW', add to rwysDone
        testId = tRow[6]
        if ( not( rcipId in rwysDone) ):
          if ( testId == rcipId ) :
            outpRway( tRow)
            rwysDone.append(testId)
      print( '</runway>\n')
  xTree = etree.ElementTree(xPropl)
  #print( etree.tostring( xTree, pretty_print=True ))
  # full Path must be created beforehand
  #outpPath = ("%s/%s/%s/%s/%s.threshold.xml" % (outpDirp, thisIcao[0], thisIcao[1], thisIcao[2], thisIcao))
  outpPath = ("%s/%s.threshold.xml" % (outpDirp, thisIcao))
  #print(outpPath)
  with open(outpPath, "wb") as outpFile:
    xTree.write(outpFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
    outpFile.close()
    
def mill_locs() :
  """ Retrieve data from database localizer table """
  global airpId, magnVari, outpDirp
  config   = load_config()
  xPropl = etree.Element("PropertyList")
  #
  with dbConn.cursor() as cur:
    # query runway table
    tQuery = "SELECT * FROM cycle2403.localizer \
              WHERE airport_identifier='%s'" % airpId
    cur.execute( tQuery)
    allRows = cur.fetchall()
  for aRow in allRows :
    print( aRow)
    



###
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
  mill_thresholds()
  mill_locs()
