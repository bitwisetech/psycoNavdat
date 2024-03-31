#!/usr/bin/env python
import psycopg2, getopt, sys

def normArgs(argv):
  global Icao, magnVari, locsXmlOpen
  global cifsAll, fldrTree, multiPass, outpDirp, specPFid, verbose, wantHelp
# fallback values
  Icao      = 'KATL'
  magnVari  =  6.00
  outpDirp  = '/data/Airports'
  specPFid  = './listIcao.txt'
  cifsAll   = 0
  fldrTree  = 0
  multiPass = 0
  verbose   = 0
  wantHelp  = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:chmo:s:tv", \
      ["airport=", "cifsAll", "help", "multiPass",  "outpPath=" , "specFile=", "--tree", "--verbose" ] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ('-a', "--airport"):
      Icao  = arg
    if   opt in ('-c', "--cifsAll"):
      cifsAll = 1
    if   opt in ('-h', "--help"):
      wantHelp = 1
    if   opt in ('-m', "--multiPass"):
      multiPass = 1
    if   opt in ("-o", "--outpPath"):
      outpDirp  = arg
    if   opt in ("-s", "--specFile"):
      specPFid  = arg
    if   opt in ('-t', "--tree"):
      fldrTree = 1
    if   opt in ('-v', "--verbose"):
      verbose = 1
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
              WHERE airport_identifier='%s' " % tIcao
    cur.execute( tQuery)
    row = cur.fetchone()
    if ( cur.rowcount != 1 ) :
      print("Info: non-singleton Airport at %s " % tIcao )
      if ( verbose > 0 ):
        print('Query: ', tQuery)
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
  if (mHdng == '') :
    tHdng = ''
  else: 
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
  if (tHdng == '') :
    xHdng.text = ''
  else : 
    xHdng.text = str("%3.1f" %  tHdng )
  xDisp = etree.SubElement( xThrs, "displ-m")
  xDisp.text = str( "%3.2f" % mDisp )
  xStop = etree.SubElement( xThrs, "stopw-m")
  xStop.text = str( "%3.2f" % mStop )
  if ( verbose > 0 ) :
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
  if ( verbose > 0 ) :
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
  if ( cur.rowcount > 0 ) :
    # Each Rway in Icao:   
    for aRow in allRows :
      rwayIcao = ''
      rwayIcao = aRow[3]
      rwayRWnn   = aRow[6]
      # Every Rwy gets a single entry in threshold.xml
      if (not( rwayRWnn in rwysDone)) :
        if ( verbose > 0 ) :
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
        #   Discard C/L/R and discard single char NSEW water landings 
        idLast = rwayRWnn[len(rwayRWnn)-1]
        if ( (len(rwayRWnn) > 1) and not (rwayRWnn.isalpha())) :
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
                        if ( verbose > 0 ) :
                          print( '\nNew  <runway>')
                        locsRwayOpen =1 
                      else :  
                        if ( verbose > 0 ) :
                          print( '\nOpen <runway>')
                      parseLocs( lRow, locsRway )
                      locsRwayOpen = 0
                      if ( verbose > 0 ) :
                        print( '</runway>')
  ## Ensure given Icao was found in cifs
  if ( not (rwayIcao == '' )) :
    thldTree = etree.ElementTree(xThlds)
    if ( verbose > 0 ) :
      print( etree.tostring( thldTree, pretty_print=True ))
    # 
    if ( fldrTree > 0 ) :
      if (( len(rwayIcao) == 4)) :
        thldXmlFid = ("%s/%s/%s/%s/%s.threshold.xml" % (outpDirp, rwayIcao[0], rwayIcao[1], rwayIcao[2], rwayIcao))
      else:  
        thldXmlFid = ("%s/%s/%s/%s.threshold.xml" % (outpDirp, rwayIcao[0], rwayIcao[1],              rwayIcao))
    else:     
      thldXmlFid = ("%s/%s.threshold.xml" % (outpDirp, rwayIcao))
    #print(thrsXmlFid)
    with open(thldXmlFid, "wb") as thldFile:
      thldTree.write(thldFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
      thldFile.close()
    # 
    if ( locsPropOpen > 0 ) :  
      if ( fldrTree > 0 ) :
        if (( len(rwayIcao) == 4)) :
          locsXmlFid = ("%s/%s/%s/%s/%s.ils.xml" % (outpDirp, rwayIcao[0], rwayIcao[1], rwayIcao[2], rwayIcao))
        else :   
          locsXmlFid = ("%s/%s/%s/%s.ils.xml" % (outpDirp, rwayIcao[0], rwayIcao[1],              rwayIcao))
      else:    
        locsXmlFid = ("%s/%s.ils.xml" % (outpDirp, rwayIcao))
      locsTree = etree.ElementTree(locsProp)
      if ( verbose > 0 ) :
        print( etree.tostring( locsProp, pretty_print=True ))
      with open(locsXmlFid, "wb") as locsFile:
        locsTree.write(locsFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
        locsFile.close()
      locsPropOpen = 0 

###
if __name__ == '__main__':
  normArgs(sys.argv[1:])
  if (wantHelp > 0 ) :
    mName = sys.argv[0]
    print(" \n ")
    print("    ")
    print(" %s : Flightgear threshold, ils .xml files from CIFS database" % sys.argv[0] )
    print("                                                                   ")
    print("Prerequ: Install PyARINC424 and build the ARINC242 postsegrsql database  ")
    print("  ref:  https://github.com/robertjkeller/PyARINC424  ")
    print("                                                                   ")
    print("         Install and configure psycopg2 Python database adapter  ")
    print("  ref:  https://pypi.org/project/psycopg2/  ")
    print("    ( For Fedora39 the binary -bin package was used   ")
    print("                                                                    ")
    print("  Copy these scripts into psycopg2/env folder and execute from there  ")
    print("  Create a folder: psycopgs/env/Airports as a default output folder ")
    print("                                                                    ")
    print(" %s : Options: " % sys.argv[0] )
    print("   -a --airport [ ICAO for single airport ")
    print("          e.g %s -a KATL" %  mName  )
    print("   -h --help    Print this help")
    print("   -m --multiPass Create multiple entries from spec file ")
    print("          use default specList.txt or -s to specify ")
    print("   -o --outpPath [somePath ]  Specify Pathname for output ( no TrailSlash, noFileId ) ")
    print("          e.g    %s -a KATL -o ~/Airports " %  mName   )
    print("   -s --specfile [PAth/FileID] List of Airport ICAO names for processing ")
    print("          INFO: message is output for airport has not a single entry in database ")
    print("   -t --tree  Use a pre-created folder tree , like terrasync/Airports ")
    print("          (Hint To create an empty tree: copy terrasync/Airports entirely,  ")
    print("           and then, with care, use rsync -r --remove-source-files newTree ./dump ")
    print("           then delete ./dump leaving an empty tree structure in newTree" )
    print("                                                                    ")
    print("   -v --verbose Outputs console printouts in addition to writing xml ")
    print("                                                                    ")
    print("   Python scripts: qAirp.py, qAlft.py, qLocs.py, qRwys.py           ")
    print("          are for exploring the database, use -a ICAO for console   ")
    print("          output of single database queries                         ")
    print("                                                                    ")

  else : 
    from config import load_config
    from lxml import etree
    # see psycopg2 for creating config file 
    config  = load_config()
    try:
      dbConn = psycopg2.connect(**config)
    except (Exception, psycopg2.DatabaseError) as error:
      print(error)
    if (cifsAll > 0 ) :
      with dbConn.cursor() as cur:
        # query runway table
        tQuery = "SELECT * FROM cycle2403.airport"
        cur.execute( tQuery)
        allRows = cur.fetchall()
      # Each Rway in Icao:   
      for aRow in allRows :
        cIcao = aRow[3]
        print (cIcao)
        get_magnVari(str(cIcao))
        mill_rwys(str(cIcao))
    else: 
      if (multiPass > 0 ) :
        # Run through spec file for multiple airports    
        with open(specPFid, 'r') as listFile:
          for listLine in listFile:
            ### Using fgLogErrs.txt error logout: 
            ##if ( '/runway:' in listLine ) :
              ##linePosn  = listLine.find ('/runway:')
              ##restLine  = listLine[ (linePosn + 8):]
              ##spacePosn = restLine.find( ' ')
              ##listIcao  = restLine[0:spacePosn]
              ## print (listIcao)
              ##get_magnVari(listIcao)
              ##mill_rwys(listIcao)
            ## Using listIcao.txt : List of plain Icao entries
            listIcao = listLine.rstrip()  
            get_magnVari(listIcao)
            mill_rwys(listIcao)
      else :
        # Single query 
        get_magnVari(Icao)
        mill_rwys(Icao)
