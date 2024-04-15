#!/usr/bin/env python
import psycopg2, getopt, sys
from config import load_config

global compAll, verbose, navId, showHelp

# fallback values
navId     = 'LFV'
a424ini   = "a424db.ini"
x810ini   = "x810db.ini"
a424Schem = 'cycle2403'
x810Schem = 'cyclexp810'
#
navdFlag  = 0
compAll  = 1
compType = 'vhf'
showHelp = 0
listFlag = 1
verbose  = 0
#
def normArgs(argv) :
  global compAll, compType, verbose, navId, showHelp
  # get args
  try:
    opts, args = getopt.getopt(argv, "hi:lnt:v", \
      ["help", "id=", "list",  "type=", "verbose" ] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ('-h', "--help"):
      showHelp = 1
    if   opt in ("-i", "--id"):
      navId  = arg
      compAll  = 0
    if   opt in ("-l", "--list"):
      listFlag = 1
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
    tHdng = float([(len(tStr) - 2)]) / 10.0
  else:
    tHdng = float([(len(tStr) - 1)]) / 10.0  + magnDecl
  return(tHdng)

def magnDecl( tStr) :
  tDecl = float(tStr[1:]) / 10.0
  if ( tStr[0] == 'W' ):
    tDecl *= -1
  return(tDecl)

def aVhfToNavd ( t424Row, navdatHndl) :
  aSect = t424Row[2]
  aSubs = t424Row[3]
  aClas = t424Row[10]
  if (aSect == 'D') :
    if not (t424Row[11] == '' ) :
      navdLati = ( "%-02.8f" % (deciLati( t424Row[11]))).rjust(12, ' ')
    if not (t424Row[12] == '' ) :
      navdLong = ( "%-03.8f" % (deciLong( t424Row[12]))).rjust(13, ' ')
    navdDecl = ( "%6i"  % magnDecl(t424Row[16])).rjust( 6, ' ')
    if not (t424Row[17] == '' ) :
      navdElev = ( "%6i"  % int(t424Row[17])).rjust( 6, ' ')
    else :
      navdElev = '     0'
    navdFreq = (t424Row[9][0:5]).rjust( 5, ' ')
    navdClas = t424Row[10]
    navdRnge = '  0'
    if (navdClas[2:3] == 'T') :
      navdRnge = ' 25'
    if (navdClas[2:3] == 'L') :
      navdRnge = ' 40'
    if (navdClas[2:3] == 'H') :
      navdRnge = '130'
    navdNuse = '   0.0'
    navdIden = t424Row[6].ljust( 4, ' ')
    #
    if (aSubs == 'B') :
      # 'D' 'B' : NDB Navaid
      navdCode = '2 '
      nameQual = 'NDB'
      navdName = ("%s %s" % ((t424Row[15].ljust( 4, ' ')), nameQual))
      navdLine = ("%s %s %s %s %s %s %s %s %s\n" %  \
      (navdCode, navdLati, navdLong, navdElev, navdFreq, \
      navdRnge, navdNuse, navdIden, navdName ))
      if verbose :
        print( navdLine)
      if navdFlag :
        addnHndl.write( navdLine)
    else :
      # 'D' ' ' : VOR or VORDME or TACAN, key off VHF Class : Line[11]
      navdCode = '3 '
      if ( 'V' in aClas) :
        if ( 'D' in aClas) :
          nameQual = 'VOR-DME'
        else :
          if ( 'T' in aClas) :
            nameQual = 'VORTAC'
          else :
            nameQual = 'VOR'
        # VOR or VOR-DME :  Code 3 Line
        navdName = ("%s %s" % ((t424Row[22].ljust( 4, ' ')), nameQual))
        navdLine = ("%s %s %s %s %s %s %s %s %s\n" %  \
        (navdCode, navdLati, navdLong, navdElev, navdFreq, \
        navdRnge, navdDecl, navdIden, navdName ))
        if verbose :
          print( navdLine)
        if navdFlag :
          addnHndl.write( navdLine)
        if not(t424Row[14] == '' ) :
          # DME portion of VOR-DME
          navdCode = '12'
          navdLati = ( "%-02.8f" % (deciLati( t424Row[14]))).rjust(12, ' ')
          navdLong = ( "%-03.8f" % (deciLong( t424Row[15]))).rjust(13, ' ')
          navdLine = ("%s %s %s %s %s %s %s %s %s\n" %  \
          (navdCode, navdLati, navdLong, navdElev, navdFreq, \
          navdRnge, navdDecl, navdIden, navdName ))
          if verbose :
            print( navdLine)
          if navdFlag :
            addnHndl.write( navdLine)
      else :
        navdCode = '13'
        if ( 'T' in aClas) :
          nameQual = 'TACAN'
        if ( 'D' in aClas) :
          nameQual = 'DME'
        navdLati = ( "%-02.8f" % (deciLati( t424Row[14]))).rjust(12, ' ')
        navdLong = ( "%-03.8f" % (deciLong( t424Row[15]))).rjust(13, ' ')
        navdIden = t424Row[13].ljust( 4, ' ')
        navdName = ("%s %s" % ((t424Row[22].ljust( 4, ' ')), nameQual))
        navdLine = ("%s %s %s %s %s %s %s %s %s\n" %  \
        (navdCode, navdLati, navdLong, navdElev, navdFreq, \
        navdRnge, navdDecl, navdIden, navdName ))
        if verbose :
          print( navdLine)
        if navdFlag :
          addnHndl.write( navdLine)
  #

def compVhfs(tNavId):
  """ Retrieve data from the navaid tables """
  a424_config = load_config(filename=a424ini)
  x810_config = load_config(filename=x810ini)
  a424Table   = 'vhf_navaid'
  x810Table   = 'vhf_navaid'
  aItemName   = 'vor_Identifier'
  xItemName   = 'vor_Identifier'
  a424_schTbl  = "%s.%s" %  (a424Schem, a424Table)
  x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
  listLine = ("ID: %s  " % tNavId )
  a424Row = ''
  try:
    with psycopg2.connect(**a424_config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
        % (a424_schTbl, aItemName, tNavId)
        cur.execute(tQuery)
        if not (cur.rowcount == 1 ):
          if ( verbose > 0 ):
            print("%s ID: %s Has Rowcount of %i " % \
            ( a424Schem , navId, cur.rowcount))
          listLine = ( " %s aRowcount: %i " % \
          (listLine, cur.rowcount ))
          a424Lati = 0
          a424Long = 0
          a424Freq =  ''
          a424Decl = 999
        else :
          a424Row = cur.fetchone()
          if ( verbose > 0 ):
            print(a424Row)
          if (a424Row[11] == ''):
            if verbose :
              print ( tNavId, "  a424Lati Blank")
            a424Lati = 99
          else :
            a424Lati = deciLati( a424Row[11])
          if (a424Row[12] == ''):
            if verbose :
              print (tNavId, "  a424Long Blank")
            a424Long = 999
          else :
            a424Long = deciLong( a424Row[12])
          # a424 Lat, Lon blank: try for non-VOR DME
          if ( (a424Row[11] == '' ) and (a424Row[12] == '')) :
            x810_schTbl  = "%s.ndat_dme" %  (x810Schem)
            xItemName = "DME_Identifier"
            a424Lati = deciLati( a424Row[14])
            a424Long = deciLong( a424Row[15])
          else :
            x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
          a424Freq =         ( a424Row[9])
          a424Decl = magnDecl( a424Row[16])
          if (verbose > 0) :
            print ( "lat : %f  lon : %f" % \
            ( (a424Lati), (a424Long)))

  except (Exception, psycopg2.DatabaseError) as error:
    print(error)

  try:
    with psycopg2.connect(**x810_config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
        % (x810_schTbl, xItemName, tNavId)
        cur.execute(tQuery)
        if not ( cur.rowcount == 1 ):
          if ( verbose > 0 ):
            print("%s ID: %s Has Rowcount of %i " % \
            ( x810Schem , navId, cur.rowcount))
          listLine = ( " %s xRowcount: %i " % \
          (listLine, cur.rowcount ))
          x810Lati = 0
          x810Long = 0
          x810Freq =  ''
          x810Decl = 999
        else :
          mismatch = 0
          listLine = ("VHF %s %s" % (a424Row[5], a424Row[6]))
          x810Row = cur.fetchone()
          if (verbose > 0) :
            print(x810Row)
          if ( x810Row[1] == '' ):
            print ( tNavId, "  x810Lati Blank")
          if ( x810Row[2] == '' ):
            print ( tNavId, "  x810Long Blank")
          x810Lati = float(x810Row[1])
          x810Long = float(x810Row[2])
          x810Freq =      ( x810Row[4])
          x810Decl = float( x810Row[6])
          diffLati = abs(x810Lati - a424Lati)
          diffLong = abs(x810Long - a424Long)
          if (verbose > 0) :
            print ( "lat : %f  lon : %f" % \
            ( (x810Lati), (x810Long)))
            print ( "\nlat diff: %f  lon diff: %f" % \
            ( diffLati, diffLong))
          #
          if ( (x810Freq == a424Freq) and (x810Decl == a424Decl) \
          and (diffLati < 0.0001) and (diffLong < 0.0001) ) :
            if (verbose > 0) :
              print (" %s Matches OK " % tNavId)
          else :
            if ((diffLati > 0.0001 ) or (diffLong > 0.0001 ) ) :
              mismatch = 1
              listLine = ( "%s aLatLon: ll=%f,%f  xLatLon: ll=%f,%f " % \
              (listLine, a424Lati, a424Long, x810Lati, x810Long ))
            if not (x810Freq == a424Freq) :
              mismatch = 1
              listLine = ( "%s aFreq: %s  xFreq: %s " % \
              (listLine, a424Freq, x810Freq ))
            if (a424Decl != x810Decl)  :
              mismatch = 1
              listLine = ( "%s aDecl: %f  xDecl: %f " % \
              (listLine, a424Decl, x810Decl))
            if (mismatch > 0) :
              if (verbose > 0) :
                print ("%s Mismatch %s " % (tNavId, listLine))
              #
              if listFlag :
                listHndl.write("%s\n" % listLine)
              aVhfToNavd ( a424Row, addnHndl)
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)

def aNdbToNavd ( t424Row, navdatHndl) :
  aSect = t424Row[2]
  aSubs = t424Row[3]
  aClas = t424Row[10]
  if ( (aSect == 'D') and (aSubs == 'B')) :
    # 'D' 'B' : NDB Navaid
    navdCode = '2 '
    nameQual = 'NDB'
    if not (t424Row[11] == '' ) :
      navdLati = ( "%-02.8f" % (deciLati( t424Row[11]))).rjust(12, ' ')
    if not (t424Row[12] == '' ) :
      navdLong = ( "%-03.8f" % (deciLong( t424Row[12]))).rjust(13, ' ')
    navdDecl = ( "%6i"  % magnDecl(t424Row[13])).rjust( 6, ' ')
    navdElev = ( "     0")
    navdFreq = (t424Row[9][1:4]).rjust( 5, ' ')
    navdClas = t424Row[10]
    navdRnge = '  0'
    if (navdClas[1:3] == 'H') :
      navdRnge = ' 75'
    if (navdClas[2:3] == ' ') :
      navdRnge = ' 50'
    if (navdClas[2:3] == 'M') :
      navdRnge = ' 25'
    if (navdClas[2:3] == 'L') :
      navdRnge = ' 15'
    navdNuse = '   0.0'
    navdIden = t424Row[6].ljust( 4, ' ')
    navdName = ("%s %s" % ((t424Row[15].ljust( 4, ' ')), nameQual))
    navdLine = ("%s %s %s %s %s %s %s %s %s\n" %  \
    (navdCode, navdLati, navdLong, navdElev, navdFreq, \
    navdRnge, navdNuse, navdIden, navdName ))
    if verbose :
      print( navdLine)
    if navdFlag :
      addnHndl.write( navdLine)
  #

def compNdbs(tNavId):
  """ Retrieve data from the navaid tables """
  a424_config = load_config(filename=a424ini)
  x810_config = load_config(filename=x810ini)
  a424Table   = 'ndb_navaid'
  x810Table   = 'ndb_navaid'
  aItemName   = 'NDB_Identifier'
  xItemName   = 'NDB_Identifier'
  a424_schTbl  = "%s.%s" %  (a424Schem, a424Table)
  x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
  listLine = ("ID: %s  " % tNavId )
  a424Row = ''
  try:
    with psycopg2.connect(**a424_config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
        % (a424_schTbl, aItemName, tNavId)
        cur.execute(tQuery)
        if not (cur.rowcount == 1 ):
          if ( verbose > 0 ):
            print("%s ID: %s Has Rowcount of %i " % \
            ( a424Schem , navId, cur.rowcount))
          listLine = ( " %s aRowcount: %i " % \
          (listLine, cur.rowcount ))
          a424Lati = 0
          a424Long = 0
          a424Freq =  ''
          a424Decl = 999
        else :
          a424Row = cur.fetchone()
          if ( verbose > 0 ):
            print(a424Row)
          if (a424Row[11] == ''):
            if verbose :
              print ( tNavId, "  a424Lati Blank")
            a424Lati = 99
          else :
            a424Lati = deciLati( a424Row[11])
          if (a424Row[12] == ''):
            if verbose :
              print (tNavId, "  a424Long Blank")
            a424Long = 999
          else :
            a424Long = deciLong( a424Row[12])
          # a424 Lat, Lon blank: try for non-VOR DME
          if ( (a424Row[11] == '' ) and (a424Row[12] == '')) :
            x810_schTbl  = "%s.ndat_dme" %  (x810Schem)
            xItemName = "DME_Identifier"
            a424Lati = deciLati( a424Row[14])
            a424Long = deciLong( a424Row[15])
          else :
            x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
          a424Freq = a424Row[9][1:4]
          a424Decl = magnDecl( a424Row[13])
          if (verbose > 0) :
            print ( "lat : %f  lon : %f" % \
            ( (a424Lati), (a424Long)))

  except (Exception, psycopg2.DatabaseError) as error:
    print(error)

  try:
    with psycopg2.connect(**x810_config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
        % (x810_schTbl, xItemName, tNavId)
        cur.execute(tQuery)
        if not ( cur.rowcount == 1 ):
          if ( verbose > 0 ):
            print("%s ID: %s Has Rowcount of %i " % \
            ( x810Schem , navId, cur.rowcount))
          listLine = ( " %s xRowcount: %i " % \
          (listLine, cur.rowcount ))
          x810Lati = 0
          x810Long = 0
          x810Freq =  ''
        else :
          mismatch = 0
          listLine = ("NDB %s %s" % (a424Row[5], a424Row[6]))
          x810Row = cur.fetchone()
          if (verbose > 0) :
            print(x810Row)
          if ( x810Row[1] == '' ):
            print ( tNavId, "  x810Lati Blank")
          if ( x810Row[2] == '' ):
            print ( tNavId, "  x810Long Blank")
          x810Lati = float(x810Row[1])
          x810Long = float(x810Row[2])
          x810Freq =      ( x810Row[4])
          diffLati = abs(x810Lati - a424Lati)
          diffLong = abs(x810Long - a424Long)
          if (verbose > 0) :
            print ( "lat : %f  lon : %f" % \
            ( (x810Lati), (x810Long)))
            print ( "\nlat diff: %f  lon diff: %f" % \
            ( diffLati, diffLong))
          #
          if ( (x810Freq == a424Freq) \
          and (diffLati < 0.0001) and (diffLong < 0.0001) ) :
            if (verbose > 0) :
              print (" %s Matches OK " % tNavId)
          else :
            if ((diffLati > 0.0001 ) or (diffLong > 0.0001 ) ) :
              mismatch = 1
              listLine = ( "%s aLatLon: ll=%f,%f  xLatLon: ll=%f,%f " % \
              (listLine, a424Lati, a424Long, x810Lati, x810Long ))
            if not (x810Freq == a424Freq) :
              mismatch = 1
              listLine = ( "%s aFreq: %s  xFreq: %s " % \
              (listLine, a424Freq, x810Freq ))
            if (verbose > 0) :
              print ("%s Mismatch %s " % (tNavId, listLine))
            #
            if (mismatch > 0) :
              if listFlag :
                listHndl.write("%s\n" % listLine)
              if ( verbose > 0 ) :
                print( listLine)
              aNdbToNavd ( a424Row, addnHndl)
  except (Exception, psycopg2.DatabaseError) as error:
      print(error)

if __name__ == '__main__':
  normArgs(sys.argv[1:])
  #
  if (showHelp > 0 ) :
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
    print("  then differences are noted in xxx-list.txt and entries are ")
    print("  appended to xxx-nav.dat ")
    print("  ")
    print(" Options :")
    print("   -h --help Print this help ")
    print("   -i --id=  Compare arinc vs x810 for this single navId ( else compare all ")
    print("   -l --list Append output for single id, rewrite output to xxx-list.txt ")
    print("   -n --navd Append output for single id, rewrite output to xxx-nav.dat ")
    print("   -t --type Specify 'ndb or 'vhf' (default) for navdb table and 'xxx-' output ")
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
  else :
    if (compType == 'ndb') :
      listPFId  = "./ndb-mismatch.txt"
      listPFId  = "./ndb-list.txt"
      addnPFId  = "./ndb-nav.dat"
      a424Table = 'ndb_navaid'
    else :
      listPFId  = "./vhf-mismatch.txt"
      listPFId  = "./vhf-list.txt"
      addnPFId  = "./vhf-nav.dat"
      a424Table = 'vhf_navaid'
    #
    if compAll :
      listHndl  = open( listPFId, 'w' )
      addnHndl  = open( addnPFId, 'w' )
      listFlag  = 1
      navdFlag   = 1
      #
      a424_schTbl  = "%s.%s" %  (a424Schem, a424Table)
      a424_config  = load_config(filename=a424ini)
      try:
        with psycopg2.connect(**a424_config) as listConn:
          with listConn.cursor() as listCurs:
            listQuery = "SELECT * FROM %s " \
            % (a424_schTbl)
            listCurs.execute(listQuery)
            print("rowcount: ", listCurs.rowcount)
            row = listCurs.fetchone()
            while row is not None:
              navId = row[6]
              if (compType == 'ndb') :
                compNdbs(navId)
              else :
                compVhfs(navId)
              #print(row)
              row = listCurs.fetchone()
      except (Exception, psycopg2.DatabaseError) as error:
          print(error)
      listHndl.close()
      addnHndl.close()
    else:
      if (listFlag > 0 ) :
        listHndl  = open( listPFId, 'a' )
      if (navdFlag > 0 ) :
        addnHndl  = open( listPFId, 'a' )
      if (compType == 'ndb') :
        compNdbs(navId)
      else :
        compVhfs(navId)
  #
