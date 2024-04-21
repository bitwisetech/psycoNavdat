#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

global compAll, verbose, a424Icao, wantHelp

# fallback values
a424Icao  = 'KATL'
navId     = 'LFV'
a424ini   = "a424db.ini"
x810ini   = "x810db.ini"
a424Schem = 'cycle2403'
x810Schem = 'cyclexp810'
#
navdFlag  = 0
compAll  = 1
compType = 'loc'
wantHelp = 0
logfFlag = 1
verbose  = 0
#
def normArgs(argv) :
  global compAll, compType, verbose, a424Icao, wantHelp, navdFlag
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:hlnt:v", \
      ["airport=", "help", "logf",  "type=", "verbose" ] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ('-h', "--help"):
      wantHelp = 1
    if   opt in ("-a", "--airport"):
      a424Icao  = arg
      compAll  = 0
    if   opt in ("-l", "--logf"):
      logfFlag = 1
    if   opt in ("-n", "--navd"):
      navdFlag  = 1
    if   opt in ("-t", "--type"):
      compType = arg
    if   opt in ("-v", "--verbose"):
      verbose = 1
  #

def deciLati( tStr) :
  # input NDDMMSSSS
  tDeci  = int( tStr[1:3] )
  tDeci += float (tStr[3:5]) /60
  tDeci += float (tStr[5:]) / ( 3600 * 100 )
  if (tStr[0] == 'S') :
    tDeci *= -1
  return ( tDeci)

def deciLong( tStr) :
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
      return(Hdng - magnDecl)
    else:
      return(999)

def trueHdng( tStr, magnVari):
  if  ( tStr[(len(tStr) - 1)] == 'T' ):
    tHdng = float(tStr[0:(len(tStr) - 2)]) / 10.0
  else:
    tHdng = float(tStr[0:(len(tStr) - 1)]) / 10.0  + magnVari
  return(tHdng)

def magnDecl( tStr) :
  tDecl = float(tStr[1:]) / 10.0
  if ( tStr[0] == 'W' ):
    tDecl *= -1
  return(tDecl)

def aLocToNavd ( LTN_aRow, navdatHndl) :
  # xp810: Rowc 4/5, Lat, Lon, ElFt, FMHz, RngNM, BngT, Iden, ICAO, RWay, Name-Type
  aSect = LTN_aRow[2]
  aSubs = LTN_aRow[4]
  aCatg = LTN_aRow[6]
  if (aSect == 'P') :
    if not (LTN_aRow[10] == '' ) :
      navdLati = ( "%-02.8f" % (deciLati( LTN_aRow[10]))).rjust(12, ' ')
    if not (LTN_aRow[11] == '' ) :
      navdLong = ( "%-03.8f" % (deciLong( LTN_aRow[11]))).rjust(13, ' ')
    if not (LTN_aRow[21] == '' ) :
      navdElev = ( "%6i"  % int(LTN_aRow[21])).rjust( 6, ' ')
    else :
      navdElev = '     0'
    navdDecl = magnDecl(LTN_aRow[20])
    trueBrng = trueHdng( LTN_aRow[12],  navdDecl )
    navdBngT = ( "%3.3f" % trueBrng).rjust(11)
    navdFreq = (LTN_aRow[8][0:5]).rjust( 5, ' ')
    navdIden = LTN_aRow[5].ljust( 4, ' ')
    navdIcao = LTN_aRow[3].ljust( 4, ' ')
    navdRway = LTN_aRow[9][2:].ljust(3)
    navdName = 'Undefined'
    if (aCatg == '0') :
      navdName = 'LOC'
      navdCode =  '5'
      navdRnge =  ' 18'
    if (aCatg == '1') :
      navdName = 'ILS Cat I'
      navdCode =  '4'
      navdRnge =  ' 18'
    if (aCatg == '2') :
      navdName = 'ILS Cat II'
      navdCode =  '4'
      navdRnge =  ' 25'
    if (aCatg == '3') :
      navdName = 'ILS Cat III'
      navdCode =  '4'
      navdRnge =  ' 35'
    if (aCatg == 'L') :
      navdName = 'LDA with GS'
      navdCode =  '5'
      navdRnge =  ' 18'
    if (aCatg == 'A') :
      navdName = 'LDA  no  GS'
      navdCode =  '5'
      navdRnge =  ' 18'
    if (aCatg == 'SL') :
      navdName = 'SDF with GS'
      navdCode =  '5'
      navdRnge =  ' 18'
    if (aCatg == 'F') :
      navdName = 'SDF  no  GS'
      navdCode =  '5'
      navdRnge =  ' 18'
    #
    navdLine = ("%s %s %s %s %s %s %s %s %s %s %s\n" %  \
    (navdCode, navdLati, navdLong, navdElev, navdFreq, navdRnge, \
     navdBngT, navdIden, navdIcao, navdRway, navdName ))
    if verbose :
      print( 'LOC Navd:', navdLine)
    if navdFlag :
      addnHndl.write( navdLine)
    #

def aGSToNavd ( GTN_aRow, navdatHndl) :
  if not (GTN_aRow[13] == '' ) :
    # GS: RCode, Lat, Lon, ElFt, Freq, Rnge, Angl+Brng, Id, Icao, Rwy, Name
    navdCode =  '6'
    navdLati = ( "%-02.8f" % (deciLati(GTN_aRow[13]))).rjust(12, ' ')
    navdLong = ( "%-03.8f" % (deciLong(GTN_aRow[14]))).rjust(13, ' ')
    navdElev = ( "%i"      % int(GTN_aRow[22])).rjust( 6, ' ')
    navdFreq = (GTN_aRow[8][0:5]).rjust( 5, ' ')
    navdRnge = ' 10'
    navdAngl = GTN_aRow[19].rjust( 3, ' ')
    navdBngT = ( "%3.3f" % (int( GTN_aRow[12])/10.0)).rjust(7)
    navdIden = GTN_aRow[5].ljust( 4, ' ')
    navdIcao = GTN_aRow[3].ljust( 4, ' ')
    navdRway = GTN_aRow[9][2:].ljust(3)
    navdName = 'GS'
    navdLine = ("%s %s %s %s %s %s  %s%s %s %s %s %s\n" %  \
    (navdCode, navdLati, navdLong, navdElev, navdFreq, navdRnge, \
     navdAngl, navdBngT, navdIden, navdIcao, navdRway, navdName ))
    if verbose :
      print( 'GS Navd:', navdLine)
    if navdFlag :
      addnHndl.write( navdLine)
  #

def compGS(a424Row, aNavId ) :
  # Compare GS entries in a424 LOC Row with x810 rCode 6 GS entry
  #  RCode, Lat, Lon, Elev, Freq, RngNM, Angle, BngT, Iden, Icao, Rway, Name
  x810Table   = 'glideslope'
  xItemName   = 'Glide_Slope_Identifier'
  x810_config = load_config(filename=x810ini)
  x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
  try:
    with psycopg2.connect(**x810_config) as conn:
      with conn.cursor() as GSxCur:
        tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
        % (x810_schTbl, xItemName, aNavId)
        GSxCur.execute(tQuery)
        if not ( GSxCur.rowcount == 1 ):
          if ( verbose > 0 ):
            print("GS  %s ID %s x810 has Rowcount: %i " % \
            ( a424Schem , aNavId, GSxCur.rowcount))
          x810Lati = 0
          x810Long = 0
          x810Freq =  ''
          x810Decl = 999
        else :
          a424Icao = a424Row[3]
          a424Loci = a424Row[5]
          a424Rway = a424Row[9]
          a424Lati = deciLati( a424Row[13])
          a424Long = deciLong( a424Row[14])
          a424Elev =      int( a424Row[22])
          a424Freq =         ( a424Row[8])
          a424Angl =         ( a424Row[19])
          a424Rway =         ( a424Row[9][2:])
          #
          x810Row = GSxCur.fetchone()
          if (verbose > 0) :
            print( 'GS xRow:', x810Row)
          if ( x810Row[1] == '' ):
            print ( aNavId, "  x810Lati Blank")
          if ( x810Row[2] == '' ):
            print ( aNavId, "  x810Long Blank")
          x810Lati = float(x810Row[1])
          x810Long = float(x810Row[2])
          x810Elev =   int( x810Row[3])
          x810Freq =      ( x810Row[4])
          x810Angl =      ( x810Row[6][0:4])
          x810Rway =      ( x810Row[10])
          #
          logfLine = ("GS  %s %s %s" % (a424Icao, a424Loci, a424Rway))
          mismatch = 0
          diffLati = abs(x810Lati - a424Lati)
          diffLong = abs(x810Long - a424Long)
          if ((diffLati > 0.0001 ) or (diffLong > 0.0001 )) :
            mismatch = 1
            logfLine = ( "%s aLatLon: ll=%f,%f  xLatLon: ll=%f,%f " % \
            (logfLine, a424Lati, a424Long, x810Lati, x810Long ))
          if not ( a424Elev == x810Elev ) :
            mismatch = 1
            logfLine = ( "%s aElev: %i  xElev: %i " % \
            (logfLine, a424Elev, x810Elev ))
          if not ( a424Freq == x810Freq ) :
            mismatch = 1
            logfLine = ( "%s aFreq: %s  xFreq: %s " % \
            (logfLine, a424Freq, x810Freq ))
          if not ( a424Angl == x810Angl ) :
            mismatch = 1
            logfLine = ( "%s aAngl: %s  xAngl: %s " % \
            (logfLine, a424Angl, x810Angl ))
          if not ( a424Rway == x810Rway ) :
            mismatch = 1
            logfLine = ( "%s aRway: %s  xRway: %s " % \
            (logfLine, a424Rway, x810Rway ))
          if ( mismatch > 0 ) :
            if (verbose > 0) :
              print ("%s GS Mismatch %s " % (aNavId, logfLine))
            if logfFlag :
              logfHndl.write("%s\n" % logfLine)
            aGSToNavd( a424Row, addnHndl)
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)



def compLocs(tIcao):
  # compares: a424LOC~x810Loc; then a424LOC~x810LOCNoGS or a424GS~x810GS
  """ Retrieve data from the navaid tables """
  a424_config = load_config(filename=a424ini)
  x810_config = load_config(filename=x810ini)
  a424Table   = 'localizer'
  x810Table   = 'localizer'
  a424_schTbl  = "%s.%s" %  (a424Schem, a424Table)
  x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
  aItemName   = 'airport_Identifier'
  xItemName   = 'Airport_Identifier'
  a424Row = ''
  if ( tIcao == 'All') : 
    tQuery = "SELECT * FROM %s WHERE %s LIKE '%%'" \
    % (a424_schTbl, aItemName)
  else : 
    tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
    % (a424_schTbl, aItemName, tIcao)
  try:
    with psycopg2.connect(**a424_config) as conn:
      with conn.cursor() as cLaCur:
        cLaCur.execute(tQuery)
        if not (cLaCur.rowcount == 0 ):
          # One ICAO may have multiple LOCs
          a424Row = cLaCur.fetchone()
          while a424Row is not None :
            if ( verbose > 0 ):
              print( 'cLOCs aRow:', a424Row)
            a424Icao = a424Row[3]
            a424Loci = a424Row[5]
            a424Rway = a424Row[9]
            logfLine = ("LOC %s " % a424Icao)
            if (a424Row[10] == ''):
              if verbose :
                print ( a424Loci, "  a424Lati Blank")
              a424Lati = 99
            else :
              a424Lati = deciLati( a424Row[10])
            if (a424Row[11] == ''):
              if verbose :
                print (a424Loci, "  a424Long Blank")
              a424Long = 999
            else :
              a424Long = deciLong( a424Row[11])
            a424Freq =         ( a424Row[8])
            if (verbose > 0) :
              print ( "cLOCs a424 ID %s LOC LatLon: ll=%f,%f" % \
              ( a424Loci, a424Lati, a424Long))
            #
            x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
            # check each LOC for GS or No GS and set x810 table
            if     (a424Row[13] == '' ) :
              # GS Lat Field Blank: Use x810 'No GS ' table below
              x810Table = 'localizer_NoGS'
            else :
              x810Table = 'localizer'
            #
            x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
            xItemName   = 'Localizer_Identifier'
            try:
              with psycopg2.connect(**x810_config) as conn:
                with conn.cursor() as cLxCur:
                  tQuery = "SELECT * FROM %s WHERE (Airport_Identifier=\'%s\') AND (%s=\'%s\') " \
                  % (x810_schTbl, a424Icao, xItemName, a424Loci)
                  cLxCur.execute(tQuery)
                  if not ( cLxCur.rowcount == 1 ):
                    if ( verbose > 0 ):
                      print("%s ID: %s x810 has Rowcount: %i " % \
                      ( x810Schem , a424Loci, cLxCur.rowcount))
                    logfLine = ( "%s %s xRowcount: %i " % \
                    (logfLine, a424Loci, cLxCur.rowcount ))
                    x810Lati = 0
                    x810Long = 0
                    x810Freq =  ''
                    x810Decl = 999
                  else :
                    mismatch = 0
                    logfLine = ("%s %s %s " % (logfLine, a424Loci, a424Rway))
                    x810Row = cLxCur.fetchone()
                    if (verbose > 0) :
                      print('cLOCs xRow:',  x810Row)
                    if ( x810Row[1] == '' ):
                      print ( a424Loci, "  x810Lati Blank")
                    if ( x810Row[2] == '' ):
                      print ( a424Loci, "  x810Long Blank")
                    x810Lati = float(x810Row[1])
                    x810Long = float(x810Row[2])
                    x810Freq =      ( x810Row[4])
                    diffLati = abs(x810Lati - a424Lati)
                    diffLong = abs(x810Long - a424Long)
                    if (verbose > 0) :
                      print ( "cLOCs x810 ID %s LOCLat : %f  LOCLon : %f" % \
                      ( a424Loci, x810Lati, x810Long))
                      print ( "\nlat diff: %f  lon diff: %f" % \
                      ( diffLati, diffLong))
                    #
                    if ( (x810Freq == a424Freq) \
                    and (diffLati < 0.0001) and (diffLong < 0.0001) ) :
                      if (verbose > 0) :
                        print ("%s LOC Matches OK " % a424Loci)
                    else :
                      if ((diffLati > 0.0001 ) or (diffLong > 0.0001 )) :
                        mismatch = 1
                        logfLine = ( "%s aLatLon: ll=%f,%f  xLatLon: ll=%f,%f " % \
                        (logfLine, a424Lati, a424Long, x810Lati, x810Long ))
                      if not (x810Freq == a424Freq) :
                        mismatch = 1
                        logfLine = ( "%s aFreq: %s  xFreq: %s " % \
                        (logfLine, a424Freq, x810Freq ))
                      if ( mismatch > 0 ) :
                        if (verbose > 0) :
                          print ("%s LOC Mismatch %s " % (a424Loci, logfLine))
                        if logfFlag :
                          logfHndl.write("%s\n" % logfLine)
                        aLocToNavd ( a424Row, addnHndl)
                    #
                    if not (a424Row[13] == '' ) :
                      #Search x810 rowCode 6 for GS entry
                      compGS(a424Row, a424Loci )
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
            a424Row = cLaCur.fetchone()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  #  
   
def showHelp() :    
  progName = sys.argv[0]
  print(" \n ")
  print(" %s : Compare ARINC424 with Flightgear postgres databases " % progName )
  print("  ")
  print("Prerequ: ")
  print("  Install PyARINC424 and build the ARINC242     postsegrsql database  ")
  print("  Install PyNavdat   and build Flightgear xp810 postsegrsql database  ")
  print("  ")
  print("This python3 script accepts a single navaid ident or 'all navId's ")
  print("  and compares arinc424 database contents with Flightgear's xp810 data ")
  print("If Lat/Lon, Mag Declination difference exceeds thresold,       ")
  print("  or key values, e.g. staion frequencies,  differ  ")
  print("  then differences are noted in xxx-logf.txt and entries are ")
  print("  appended to xxx-nav.dat ")
  print("  ")
  print(" Options :")
  print("   -h --help Print this help ")
  print("   -a --airport=  Compare arinc vs x810 localizers for single airport ICAO ")
  print("   -l --logf Append output for single id, rewrite output to xxx-logf.txt ")
  print("   -n --navd Append output for single id, rewrite output to xxx-nav.dat ")
  print("   -t --type Specify 'loc or 'vhf' (default) for navdb table and 'xxx-' output ")
  print("   -v --verbose Log progress to console ")
  print("  ")
  print(" Example calls:")
  print("   for Single NDB Id:  %s -i AMF -t n " %  progName)
  print("   for Single VHF Id:  %s -i BRW -t v " %  progName)
  print("   for All    NDB   :  %s        -t n " %  progName)
  print("   for All    VHF Id:  %s        -t v " %  progName)
  print("  ")
  print(" Default:  Compare all vhf types  ")
  print("  ")
  print("Hint: To sort xxx-nav.dat into adds-nav.dat :   ")
  print("  cat xxx-nav.dat  | sort -k1,1r -k9,9  > vhf-adds-nav.dat  ")
  print("  ")
  print("  ")
#

if __name__ == '__main__':
  normArgs(sys.argv[1:])
  #
  if (wantHelp > 0 ) :
    showHelp()
  #
  else :
    logfPFId  = "./loc-logf.txt"
    addnPFId  = "./loc-nav.dat"
    a424Table = 'localizer'
    addnHndl  = ''
    #
    if compAll :
      logfFlag = 1
      navdFlag = 1
      a424Icao = 'All'
    if (logfFlag > 0 ) :
      logfHndl  = open( logfPFId, 'a' )
    if (navdFlag > 0 ) :
      addnHndl  = open( addnPFId, 'a' )
    compLocs(a424Icao)
    #
    if (logfFlag > 0 ) :
      logfHndl.close()
    if (navdFlag > 0 ) :
      addnHndl.close()
  #
