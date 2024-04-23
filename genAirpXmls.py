#!/usr/bin/env python
import psycopg2, getopt, os, sys


def normArgs(argv):
  global argsIcao, magnVari
  global cifsAll, fldrTree, thldTree, outpDirp, specPFId, verbose, showHelp
# fallback values
  argsIcao      = 'KATL'
  magnVari  =  6.00
  outpDirp  = './Airports'
  specPFId  = ''
  cifsAll   = 0
  fldrTree  = 0
  verbose   = 0
  showHelp  = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:cho:s:tv", \
      ["airport=", "cifsAll", "help",  "outpPath=" , "specFile=", "--tree", "--verbose" ] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ('-a', "--airport"):
      argsIcao  = arg
      cifsAll = 0
    if   opt in ('-c', "--cifsAll"):
      cifsAll = 1
    if   opt in ('-h', "--help"):
      showHelp = 1
    if   opt in ("-o", "--outPath"):
      outpDirp  = arg
    if   opt in ("-s", "--specFile"):
      specPFId  = arg
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

def ft2mtr ( tStr):
  # FF
  if ( tStr == '' ) :
    return( 0)
  else :
    tDeci  = (int(tStr) * 12 * 0.0254)
    return ( tDeci)

def mtr2ft ( tStr):
  # FF
  if ( tStr == '' ) :
    return( 0)
  else :
    tDeci  = (int(tStr) / ( 12 * 0.0254))
    return ( tDeci)

def magnHdng( tStr, magnDecl):
  Hdng = float(tStr[0:4]) / 10.0
  if  ( len(tStr) < 5 ):
    return(tHdng)
  else:
    if (tStr[4] == 'T' ) :
      mHdng = (Hdng - magnDecl)
      while ( mHdng < 0 ) :
        mHdng += 360
      return (mHdng)
    else:
      return(999)

def trueHdng( tStr, magnVari):
  if  ( tStr[(len(tStr) - 1)] == 'T' ):
    tHdng = float(tStr[0:(len(tStr) - 1)]) / 10.0
  else:
    tHdng = float(tStr[0:(len(tStr)    )]) / 10.0  + magnVari
  while ( tHdng < 0 ) :
    tHdng += 360  
  return(tHdng)

def magnDecl( tStr) :
  tDecl = float(tStr[1:]) / 10.0
  if ( tStr[0] == 'W' ):
    tDecl *= -1
  return(tDecl)

def get_magnVari( tIcao) :
  global argsIcao, magnVari, outpDirp
  with dbConn.cursor() as cur:
    # query airport table for Mag Variation
    tQuery = "SELECT * FROM cycle2403.airport \
              WHERE Airport_Identifier='%s' " % tIcao
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
  global argsIcao, magnVari, outpDirp, nvdbHndl, thrsElvM, sameIcao
  global locsProp, xThlds, xRway, xThrs, xIden, xHdng, xLati, xLong, xDisp, xStop
  tIden = tRow[6][2: ]
  mHdng = tRow[9]
  if (mHdng == '') :
    tHdng = ''
  else:
    tHdng = trueHdng( mHdng, magnVari)
  tLati = tRow[10]
  dLati = deciLati( tLati)
  tLong = tRow[11]
  dLong = deciLong( tLong)
  mElev = ft2mtr( tRow[14])
  thrsElvM = mElev
  tDisp =       ( tRow[15])
  mDisp = ft2mtr( tRow[15])
  tStop =       ( tRow[21])
  mStop = ft2mtr( tRow[21])
  xThrs = etree.SubElement( xRway, "threshold")
  xLong = etree.SubElement( xThrs, "lon")
  xLong.text = str( "%3.6f" % dLong )
  xLati = etree.SubElement( xThrs, "lat")
  xLati.text = str("%3.6f" % dLati )
  xIden = etree.SubElement( xThrs, "rwy")
  xIden.text = str( tIden )
  xHdng = etree.SubElement( xThrs, "hdg-deg")
  if (tHdng == '') :
    xHdng.text = ''
  else :
    xHdng.text = str("%3.2f" %  tHdng )
  xDisp = etree.SubElement( xThrs, "displ-m")
  xDisp.text = str( "%3.1f" % mDisp )
  xStop = etree.SubElement( xThrs, "stopw-m")
  xStop.text = str( "%3.1f" % mStop )
  if ( verbose > 0 ) :
    print( "Iden: %s  HdgT: %3.1f  dLati: %3.5f  dLong: %3.5f  mDisp: %4.1f  mStop: %4.1f" % \
    (tIden, tHdng, dLati, dLong, mDisp, mStop))

def parseLocs ( tRow, xRway) :
  global locsProp, xThlds, argsIcao, magnVari, outpDirp, thrsElvM, sameIcao
  locsRwy    = tRow[9][2:]
  locsNvId   = tRow[5]
  locsHdgT   = trueHdng( tRow[12], magnVari)
  locsLat    = deciLati( tRow[10])
  locsLon    = deciLong( tRow[11])
  locsElev   = thrsElvM
  if ( verbose > 0 ) :
    print ('\n pLocs Rwy:', locsRwy, ' ID:', locsNvId, )
  # Add fields to passed xml Runway
  xIls       = etree.SubElement( xRway, "ils")
  xLong      = etree.SubElement( xIls, "lon")
  xLong.text = str("%3.6f" % locsLon )
  xLati      = etree.SubElement( xIls, "lat")
  xLati.text = str("%3.6f" % locsLat )
  xRwy       = etree.SubElement( xIls, "rwy")
  xRwy.text  = str( locsRwy)
  xHdg       = etree.SubElement( xIls, "hdg-deg")
  xHdg.text  = str( "%3.2f" % locsHdgT)
  xElev      = etree.SubElement( xIls, "elev-m")
  xElev.text = str( "%.2f" % locsElev)
  xNvId      = etree.SubElement( xIls, "nav-id")
  xNvId.text = str( locsNvId )
  # Build XP 810 nav.dat record
  navdLati   = ( "%-02.8f" % locsLat ).rjust(12, ' ')
  navdLong   = ( "%-03.8f" % locsLon ).rjust(13, ' ')
  navdElev   = ( "%6i"  % int(mtr2ft(thrsElvM))).rjust( 6, ' ')
  navdFreq   = tRow[8].rjust( 5, ' ')
  navdRngm   = ( ' 18')
  navdHdgT   = ( "%3.3f" % locsHdgT).rjust( 11, ' ')
  navdNvId   = locsNvId.rjust( 4, ' ')
  navdAirp   = tRow[3].rjust( 4, ' ')
  navdRway   = (tRow[9][2:]).ljust( 3, ' ')
  navdDesc   = ( 'ILS-cat-I')
  navdLine   = ("4 %s %s %s %s %s %s %s %s %s %s\n" %  \
  (navdLati, navdLong, navdElev, navdFreq, navdRngm, \
  navdHdgT, navdNvId, navdAirp, navdRway, navdDesc ))
  if ( verbose > 0 ) :
    print( navdLine)
  nvdbHndl.write( navdLine)
  # If glideslope exists, Lat entry follows Loc Hdng
  if (not ( tRow[13] == '' )) :
    nvGSLati = ( "%-02.8f" % (deciLati(tRow[13]))).rjust(12, ' ')
    nvGSLong = ( "%-03.8f" % (deciLong(tRow[14]))).rjust(13, ' ')
    nvGSElev = tRow[21].rjust( 6, ' ')
    nvGSFreq = navdFreq
    nvGSRngm = ' 10'
    nvGSAngl = tRow[19].rjust( 4, ' ')
    nvGSBrng = ( "%3.3f" % locsHdgT).ljust( 7, ' ')
    nvGSNvId = navdNvId
    nvGSAirp = navdAirp
    nvGSRway = navdRway
    nvGSDesc = 'GS'
    nvGSLine =  ("6 %s %s %s %s %s %s%s %s %s %s %s\n" %  \
    (nvGSLati, nvGSLong, nvGSElev, nvGSFreq, nvGSRngm, \
    nvGSAngl, nvGSBrng, nvGSNvId, nvGSAirp, nvGSRway, nvGSDesc ))
    if ( verbose > 0 ) :
      print( nvGSLine)
    nvdbHndl.write( nvGSLine)

def millRwys(tIcao, tLocId, sameIcao):
  """ Retrieve data from database runway table """
  global magnVari, outpDirp
  global locsProp, xThlds, thldTree, xRway, xThrs, xIden, xHdng, xLati, xLong, xDisp, xStop
  rwysDone = []
  locsPropOpen = 0
  locsRwayOpen = 0
  config       = load_config()
  if not sameIcao :
    xThlds       = etree.Element("PropertyList")
  if ( tLocId == '') :
    # Pull all Rways for given A/P
    tQuery = "SELECT * FROM cycle2403.runway  \
              WHERE  Airport_Identifier='%s'" % tIcao
  else :
    tQuery = "SELECT * FROM cycle2403.runway  \
              WHERE Airport_Identifier='%s' AND LOC__MLS__GLS_Identifier = '%s'" % \
              (tIcao, tLocId )
  with dbConn.cursor() as cur:
    # query runway table
    cur.execute( tQuery)
    allRows = cur.fetchall()
  if ( cur.rowcount > 0 ) :
    # Each Rway in Icao:
    for aRow in allRows :
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
                    WHERE Airport_Identifier='%s'" % tIcao
          cur.execute( lQuery)
          locsRows = cur.fetchall()
          if ( cur.rowcount > 0) :
            for lRow in locsRows :
              locsRWnn = lRow[9]
              if ( locsRWnn == rwayRWnn ) :
                if ( locsPropOpen < 1 ) :
                  if not sameIcao :
                    locsProp = etree.Element("PropertyList")
                  locsPropOpen = 1
                locsRway = etree.SubElement(locsProp, "runway")
                locsRwayOpen = 1
                parseLocs( lRow, locsRway)
        # After parsing: xml  Prop and Rway are left open in case of recip ILS
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
                        if not sameIcao :
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
          # test done for rcip Rwy: close <runway. tag
          locsRwayOpen = 0
          if ( verbose > 0 ) :
            print( '</runway>')
  ## Ensure given Icao was found in cifs
  if ( not (rwayIcao == '' )) :
    if not sameIcao :
      thldTree = etree.ElementTree(xThlds)
    #if ( verbose > 0 ) :
      #print( etree.tostring( thldTree, pretty_print=True ))
    #
    if ( fldrTree > 0 ) :
      if (( len(rwayIcao) == 4)) :
        fldrPath   = ("%s/%s/%s/%s" % (outpDirp, rwayIcao[0], rwayIcao[1], rwayIcao[2] ))
      if (( len(rwayIcao) == 3)) :
        fldrPath   = ("%s/%s/%s" % (outpDirp, rwayIcao[0], rwayIcao[1] ))
      if (( len(rwayIcao) == 2)) :
        fldrPath   = ("%s/%s" % (outpDirp, rwayIcao[0]))
      #
      if ( not ( os.path.isdir( fldrPath ))) :
         os.makedirs( fldrPath )
      thldXmlFid = ("%s/%s.threshold.xml" % (fldrPath, tIcao))
    else:
      thldXmlFid = ("%s/%s.threshold.xml" % (outpDirp, tIcao))
    #
    with open(thldXmlFid, "wb") as thldFile:
      thldTree.write(thldFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
      thldFile.close()
    #
    if ( locsPropOpen > 0 ) :
      if ( fldrTree > 0 ) :
        if (( len(rwayIcao) == 4)) :
          locsXmlFid = ("%s/%s/%s/%s/%s.ils.xml" % (outpDirp, rwayIcao[0], rwayIcao[1], rwayIcao[2], tIcao))
        else :
          locsXmlFid = ("%s/%s/%s/%s.ils.xml" % (outpDirp, rwayIcao[0], rwayIcao[1],                 tIcao))
      else:
        locsXmlFid = ("%s/%s.ils.xml" % (outpDirp, tIcao))
      locsTree = etree.ElementTree(locsProp)
      #if ( verbose > 0 ) :
        #print( etree.tostring( locsProp, pretty_print=True ))
      with open(locsXmlFid, "wb") as locsFile:
        locsTree.write(locsFile, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1")
        locsFile.close()
      locsPropOpen = 0

###
if __name__ == '__main__':
  normArgs(sys.argv[1:])
  progName = sys.argv[0]
  if (showHelp > 0 ) :
    print(" \n ")
    print("    ")
    print(" %s : Flightgear threshold, ils .xml files from CIFS database" % profName )
    print("  ")
    print("Prerequ: Install PyARINC424 and build the ARINC242 postsegrsql database  ")
    print("  ref:  https://github.com/robertjkeller/PyARINC424  ")
    print("  ")
    print("         Install and configure psycopg2 Python database adapter  ")
    print("  ref:  https://pypi.org/project/psycopg2/  ")
    print("    ( For Fedora39 the binary -bin package was used   ")
    print("  ")
    print("  Copy these scripts into psycopg2/env folder and execute from there  ")
    print("  Create a folder: psycopgs/env/Airports as a default output folder ")
    print("  ")
    print(" %s : Options: " % progName )
    print("   -a --airport [ ICAO for single airport ")
    print("          e.g %s -a KATL" %  mName  )
    print("   -c --cifsAll Create output for complete CIFS database: All airports")
    print("          Caution: will create subdirs, 6,000+ files: 25MBy+ flat file, 50MBy+ tree ")
    print("   -h --help    Print this help")
    print("   -o --outPath [somePath ]  Specify Pathname for output ( no TrailSlash, noFileId ) ")
    print("          e.g    %s -a KATL -o ~/Airports " %  mName   )
    print("          NavData/nav/addin-nav.dat folder is created alongside this folder                                                          ")
    print("   -s --specfile [PAth/FileID] List of Airport ICAO [.. Loc Id] names for processing ")
    print("          If list contains 'ICAO '      then create all Runways entries")
    print("          If list contains 'ICAO LocId' then create entries for specified Loc")
    print("   -t --tree  Use a pre-created folder tree , like terrasync/Airports ")
    print("          (Hint To create an empty tree: copy terrasync/Airports entirely,  ")
    print("            and then, with care, use rsync -r --remove-source-files newTree ./dump ")
    print("            then delete ./dump leaving an empty tree structure in newTree" )
    print("          Subfolders will be created as needed under specified output path                                                            ")
    print("  ")
    print("   -v --verbose Outputs console printouts in addition to writing xml ")
    print("  ")
    print("   Python scripts: qAirp.py, qAlft.py, qLocs.py, qRwys.py           ")
    print("          are for exploring the database, use -a ICAO for console   ")
    print("          output of single database queries                         ")
    print("  ")

  else :
    from config import load_config
    from lxml import etree
    # see psycopg2 for creating config file
    config  = load_config()
    try:
      dbConn = psycopg2.connect(**config)
    except (Exception, psycopg2.DatabaseError) as error:
      print(error)
    # nav.dat needs header and footer; NavData is placed next to Airports folder
    nvdbPFId = ( outpDirp + '/addins-nav.dat' )
    nvdbHndl = open( nvdbPFId, 'a' )
    #
    if (cifsAll > 0 ) :
      with dbConn.cursor() as cur:
        # query runway table
        tQuery = "SELECT * FROM cycle2403.airport"
        cur.execute( tQuery)
        allRows = cur.fetchall()
      # Each Rway in Icao
      for aRow in allRows :
        cIcao = aRow[3]
        print (cIcao)
        get_magnVari(str(cIcao))
        millRwys(str(cIcao), '')
    else:
      if not ( specPFId == '' ) :
        # Run through spec file for each entry Icao [LocId] entry
        prevIcao = ''
        with open(specPFId, 'r') as specHndl:
          for specLine in specHndl:
            specList = specLine.split()
            specIcao = specList[0]
            # Determine if output file is to be new fileid
            if ( specIcao == prevIcao ) :
              sameIcao = 1
            else :
              sameIcao = 0
              prevIcao = specIcao
              #
              if ( len(specList) > 1 ) :
                specLocId = specList[1]
              else :
                specLocId = ''
              print(specIcao)
              get_magnVari(specIcao)
              millRwys(specIcao, '', sameIcao)
        specHndl.close()
      else :
        # Single query
        print(argsIcao)
        get_magnVari(argsIcao)
        millRwys(argsIcao, '')
    nvdbHndl.close()
### End
