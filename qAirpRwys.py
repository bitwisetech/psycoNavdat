#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config
from lxml import etree


def normArgs(argv):
  global Icao, magnVari, outpDirp, listPFid, locsXmlOpen
# fallback values
  Icao   = 'KAOH'
  outpDirp = '/comm/fpln/cifp/Airports'
  listPFid = '/comm/fpln/cifp/Airports/navErrs.txt'
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:d:l:", \
      ["airfId=", "listPFid", "outpDirp"] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ("-a", "--airpId"):
      Icao  = arg
    if   opt in ("-d", "--outpDirp"):
      outpDirp  = arg
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

def get_magnVari( tIcao) :
  global Icao, magnVari, outpDirp, locsXmlOpen
  with dbConn.cursor() as cur:
    # query airport table for Mag Variation
    tQuery = "SELECT * FROM cycle2403.airport \
              WHERE airport_identifier='%s'" % tIcao
    cur.execute( tQuery)
    row = cur.fetchone()
    if ( cur.rowcount != 1 ) :
      print("Error, non-singleton Airport count: ", cur.rowcount)
    else :
      tMagVar = float(row[14][1:]) / 10.0
      if ( row[14][0] != 'W' ):
        tMagVar *= -1
      magnVari = tMagVar

def parseRway ( tRow) :
  global Icao, magnVari, outpDirp, locsXmlOpen, thrsElvM
  global xThlds, xRway, xThrs, xIden, xHdng, xLati, xLong, xDisp, xStop
  tIden = tRow[6][2: ]
  mHdng = tRow[9]
  tHdng = trueHdng( mHdng)
  tLati = tRow[10]
  dLati = deciLati( tLati)
  tLong = tRow[11]
  dLong = deciLong( tLong)
  mElev = ft2Mtr( tRow[14])
  thrsElvM = mElev
  tDisp =       ( tRow[15])
  mDisp = ft2Mtr( tRow[15])
  tStop =       ( tRow[21])
  mStop = ft2Mtr( tRow[21])
  xThrs = etree.SubElement( xRway, "threshold")
  xLong = etree.SubElement( xThrs, "lon")
  xLong.text = str( "%3.5f" % dLong )
  xLati = etree.SubElement( xThrs, "lat")
  xLati.text = str("%3.5f" % dLati )
  xIden = etree.SubElement( xThrs, "rwy")
  xIden.text = str( tIden )
  xHdng = etree.SubElement( xThrs, "hdg-deg")
  xHdng.text = str("%3.1f" %  tHdng )
  xDisp = etree.SubElement( xThrs, "displ-m")
  xDisp.text = str( "%3.2f" % mDisp )
  xStop = etree.SubElement( xThrs, "stopw-m")
  xStop.text = str( "%3.2f" % mStop )
  print( "Iden: %s  HdgT: %3.1f  dLati: %3.5f  dLong: %3.5f  mDisp: %4.1f  mStop: %4.1f" % \
    (tIden, tHdng, dLati, dLong, mDisp, mStop))
    
def parseLocs ( tRow, xRway) :
  global Icao, magnVari, outpDirp, locsXmlOpen, thrsElvM
  locsRwy    = tRow[9][2:]
  locsNvId   = tRow[5]
  locsHdgT   = trueHdng( tRow[12])
  locsLat    = deciLati( tRow[10])
  locsLon    = deciLong( tRow[11])
  locsElev   = thrsElvM
  print ('\n pLocs Rwy:', locsRwy, ' ID:', locsNvId, )
  xIls       = etree.SubElement( xRway, "ils")
  xLong      = etree.SubElement( xIls, "lon")
  xLong.text  = str("%3.5f" % locsLon )
  xLati      = etree.SubElement( xIls, "lat")
  xLati.text = str("%3.5f" % locsLat )
  xRwy       = etree.SubElement( xIls, "rwy")
  xRwy.text  = str( locsRwy)
  xHdg       = etree.SubElement( xIls, "hdg-deg")
  xHdg.text  = str( "%3.1f" % locsHdgT)
  xElev      = etree.SubElement( xIls, "elev-m")
  xElev.text  = str( "%.1f" % locsElev) 
  xNvId      = etree.SubElement( xIls, "nav-id")
  xNvId.text = str( locsNvId )
  
def mill_rwys(tIcao):
  """ Retrieve data from database runway table """
  global magnVari, outpDirp, locsXmlOpen
  global xThlds, xRway, xThrs, xIden, xHdng, xLati, xLong, xDisp, xStop
  rwysDone = []
  locsPropOpen = 0
  locsRwayOpen = 0
  config   = load_config()
  xThlds = etree.Element("PropertyList")
  # Pull all Rways for given A/P 
  rwayIcao = ''
  with dbConn.cursor() as cur:
    # query runway table
    tQuery = "SELECT * FROM cycle2403.runway \
              WHERE airport_identifier='%s'" % tIcao
    cur.execute( tQuery)
    allRows = cur.fetchall()
  # Each Rway in Icao:   
  for aRow in allRows :
    rwayIcao = ''
    rwayIcao = aRow[3]
    rwayRWnn   = aRow[6]
    # Every Rwy gets a single entry in threshold.xml
    if (not( rwayRWnn in rwysDone)) :
      print( '\n', rwayIcao, ' <runway>', rwayRWnn)
      xRway = etree.SubElement(xThlds, "runway")
      parseRway( aRow)
      rwysDone.append(rwayRWnn)
      with dbConn.cursor() as cur:
        # query localizer table for ILS
        lQuery = "SELECT * FROM cycle2403.localizer \
                  WHERE airport_identifier='%s'" % tIcao
        cur.execute( lQuery)
        locsRows = cur.fetchall()
        if ( cur.rowcount > 0) :
          for lRow in locsRows :
            locsRWnn = lRow[9]
            if ( locsRWnn == rwayRWnn ) :
              if ( locsPropOpen < 1 ) :
                locsProp = etree.Element("PropertyList")
                locsPropOpen = 1
              locsRway = etree.SubElement(locsProp, "runway")
              locsRwayOpen = 1
              parseLocs( lRow, locsRway)
      # After parsing Prop and Rway are left defined in case of recip ILS      
      # Look for reciprocal to put within the same Rwy
      idLast = rwayRWnn[len(rwayRWnn)-1]
      if (idLast.isalpha()) :
        idNumb = int(rwayRWnn[2:len(rwayRWnn)-1])
        idChar = idLast
      else :
        idNumb = int(rwayRWnn[2:])
        idChar = ''
      if (idNumb > 18 ) :
        rcipNumb = idNumb - 18
      else:
        rcipNumb = idNumb + 18
      rcipChar = ''
      if (idChar == 'C') :
        rcipChar = 'C'
      if (idChar == 'L') :
        rcipChar = 'R'
      if (idChar == 'R') :
        rcipChar = 'L'
      rcipRWnn = ( "RW%02i%s" % (rcipNumb, rcipChar))
      # Find rcip rwy in list
      for tRow in allRows :
        testId = tRow[6]
        if ( not( rcipRWnn in rwysDone) ):
          if ( testId == rcipRWnn ) :
            parseRway( tRow)
            rwysDone.append(testId)
            # e.g KBOS 09/27 Only Rcip Rwy has ILS, so maybe open ils.xml 
            if ( cur.rowcount > 0) :
              for lRow in locsRows :
                locsRWnn = lRow[9]
                if ( locsRWnn == rcipRWnn ) :
                  if ( locsPropOpen < 1 ) :
                    locsProp = etree.Element("PropertyList")
                    locsPropOpen = 1
                  if ( locsRwayOpen < 1 ) :
                    locsRway = etree.SubElement(locsProp, "runway")
                    print( '\nNew  <runway>')
                    locsRwayOpen =1 
                  else :  
                    print( '\nOpen <runway>')
                  parseLocs( lRow, locsRway )
                  locsRwayOpen = 0
                  print( '</runway>')
  ## Ensure given Icao was found in cifs
  if ( not (rwayIcao == '' )) :
    thldTree = etree.ElementTree(xThlds)
    #print( etree.tostring( thldTree, pretty_print=True ))
    # full Path must be created beforehand
    #
    if (( len(rwayIcao) == 4)) :
      thldXmlFid = ("%s/%s/%s/%s/%s.threshold.xml" % (outpDirp, rwayIcao[0], rwayIcao[1], rwayIcao[2], rwayIcao))
    else:  
      thldXmlFid = ("%s/%s/%s/%s.threshold.xml" % (outpDirp, rwayIcao[0], rwayIcao[1],              rwayIcao))
    #thldXmlFid = ("%s/%s.threshold.xml" % (outpDirp, rwayIcao))
    #print(thrsXmlFid)
    with open(thldXmlFid, "wb") as thldFile:
      thldTree.write(thldFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
      thldFile.close()
    ##
    if ( locsPropOpen > 0 ) :  
      if (( len(rwayIcao) == 4)) :
        locsXmlFid = ("%s/%s/%s/%s/%s.ils.xml" % (outpDirp, rwayIcao[0], rwayIcao[1], rwayIcao[2], rwayIcao))
      else :   
        locsXmlFid = ("%s/%s/%s/%s.ils.xml" % (outpDirp, rwayIcao[0], rwayIcao[1],              rwayIcao))
      #locsXmlFid = ("%s/%s.ils.xml" % (outpDirp, rwayIcao))
      locsTree = etree.ElementTree(locsProp)
      with open(locsXmlFid, "wb") as locsFile:
        locsTree.write(locsFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
        locsFile.close()
      locsPropOpen = 0 

###
if __name__ == '__main__':
  normArgs(sys.argv[1:])
  magnVari = 15.00
  config  = load_config()
  try:
    dbConn = psycopg2.connect(**config)
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)
  with open(listPFid, 'r') as listFile:
    for listLine in listFile:
      if ( '/runway:' in listLine ) :
        linePosn  = listLine.find ('/runway:')
        restLine  = listLine[ (linePosn + 8):]
        spacePosn = restLine.find( ' ')
        findIcao  = restLine[0:spacePosn]
        #        print (findIcao)
        #
        get_magnVari(findIcao)
        #
        mill_rwys(findIcao)
