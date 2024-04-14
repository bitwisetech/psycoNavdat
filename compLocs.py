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
compType = 'loc'
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

def trueHdng( tStr):
  global magnVari
  tHdng = float(tStr[0:4]) / 10.0
  if  ( len(tStr) < 5 ):
    tHdng -= magnVari
  else:
    if ( (tStr[4]) != 'T' ) :
      tHdng -= magnVari
  return(tHdng)

def magnDecl( tStr) :
  tDecl = float(tStr[1:]) / 10.0
  if ( tStr[0] == 'W' ):
    tDecl *= -1
  return(tDecl)
  
def aLocToNavd ( t424Row, navdatHndl) :
  # xp810: Rowc 4/5, Lat, Lon, ElFt, FMHz, RngNM, BngT, Iden, ICAO, RWay, Name-Type
  aSect = t424Row[2]
  aSubs = t424Row[4]
  aCatg= t424Row[6]
  if (aSect == 'P') :
    if not (t424Row[10] == '' ) :
      navdLati = ( "%-02.8f" % (deciLati( t424Row[10]))).rjust(12, ' ')
    if not (t424Row[11] == '' ) :
      navdLong = ( "%-03.8f" % (deciLong( t424Row[11]))).rjust(13, ' ')
    if not (t424Row[21] == '' ) :
      navdElev = ( "%6i"  % int(t424Row[21])).rjust( 6, ' ')
    else : 
      navdElev = '     0'  
    navdFreq = (t424Row[8][0:5]).rjust( 5, ' ')
    navdBngT = ( "%3.3f" % (int( t424Row[12])/10.0)).rjust(11)
    navdIden = t424Row[5].ljust( 4, ' ')
    navdIcao = t424Row[3].ljust( 4, ' ')
    navdRway = t424Row[9][2:].ljust(3)
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
      print( navdLine)
    if navdFlag :  
      addnHndl.write( navdLine)
    #
 
def aGSToNavd ( t424Row, navdatHndl) :
  if not (t424Row[13] == '' ) :
    # GS: RCode, Lat, Lon, ElFt, Freq, Rnge, Angl+Brng, Id, Icao, Rwy, Name 
    navdCode =  '6' 
    navdLati = ( "%-02.8f" % (deciLati(t424Row[13]))).rjust(12, ' ')
    navdLong = ( "%-03.8f" % (deciLong(t424Row[14]))).rjust(13, ' ')
    navdElev = t424Row[21].rjust( 6, ' ')
    navdFreq = (t424Row[8][0:5]).rjust( 5, ' ')
    navdRnge = ' 10'
    navdAngl = t424Row[19].rjust( 3, ' ')
    navdBngT = ( "%3.3f" % (int( t424Row[12])/10.0)).rjust(7)
    navdIden = t424Row[5].ljust( 4, ' ')
    navdIcao = t424Row[3].ljust( 4, ' ')
    navdRway = t424Row[9][2:].ljust(3)
    navdName = 'GS'
    navdLine = ("%s %s %s %s %s %s  %s%s %s %s %s %s\n" %  \
    (navdCode, navdLati, navdLong, navdElev, navdFreq, navdRnge, \
     navdAngl, navdBngT, navdIden, navdIcao, navdRway, navdName ))
    if verbose :
      print( navdLine)
    if navdFlag :  
      addnHndl.write( navdLine)
  #

def compGS(a424Row ) :

def compLocs(tIcao):
  # compares: a424LOC~x810Loc; then a424LOC~x810LOCNoGS or a424GS~x810GS
  """ Retrieve data from the navaid tables """
  a424_config = load_config(filename=a424ini)
  x810_config = load_config(filename=x810ini)
  a424Table   = 'localizer'
  x810Table   = 'localizer'
  aItemName   = 'localizer_Identifier'
  xItemName   = 'localizer_Identifier'
  a424_schTbl  = "%s.%s" %  (a424Schem, a424Table)
  x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)
  listLine = ("ICAO: %s  " % tIcao )
  a424Row = ''
  try:
    with psycopg2.connect(**a424_config) as conn:
      with conn.cursor() as cur:
        tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
        % (a424_schTbl, aItemName, tIcao)
        cur.execute(tQuery)
        if (cur.rowcount == 0 ):
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
          One ICAO may have multiple LOCs
          a424Row = cur.fetchone()
          while a424Row is not None :
            if ( verbose > 0 ):
              print(a424Row)
            aNavId = a424Row[5]   
            if (a424Row[10] == ''):
              if verbose :
                print ( tNavId, "  a424Lati Blank")
              a424Lati = 99
            else :  
              a424Lati = deciLati( a424Row[10])
            if (a424Row[11] == ''):
              if verbose :
                print (tNavId, "  a424Long Blank")
              a424Long = 999
            else :  
              a424Long = deciLong( a424Row[11])
            x810_schTbl  = "%s.%s" %  (x810Schem, x810Table)            
            a424Freq =         ( a424Row[8])
            if (verbose > 0) :
              print ( "lat : %f  lon : %f" % \
              ( (a424Lati), (a424Long)))
            # check each LOC for GS or No GS and set x810 table
            if     (t424Row[13] == '' ) :
              # GS Lat Field Blank: Use x810 'No GS ' table below
              xItemName = 'localizer_NoGS'
            else : 
              xItemName = 'localizer'
            #
            try:
              with psycopg2.connect(**x810_config) as conn:
                with conn.cursor() as cur:
                  tQuery = "SELECT * FROM %s WHERE %s=\'%s\' " \
                  % (x810_schTbl, xItemName, aNavId)
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
                        print (" %s Matches OK " % aNavId) 
                    else :
                      if (diffLati > 0.0001 )  :
                        listLine = ( "%s aLati: %f  xLati: %f " % \
                        (listLine, a424Lati, x810Lati )) 
                      if (diffLong > 0.0001 )  :
                        listLine = ( "%s aLong: %f  xLong: %f " % \
                        (listLine, a424Long, x810Long ))
                      if not (x810Freq == a424Freq) :
                        listLine = ( "%s aFreq: %s  xFreq: %s " % \
                        (listLine, a424Freq, x810Freq ))
                      if (verbose > 0) :
                        print ("%s Mismatch %s " % (tNavId, listLine))
                      #
                      if listFlag :
                        listHndl.write("%s\n" % listLine)
                      if ( verbose > 0 ) :
                        print( listLine)
                      if (not( a424Row == '') and (navdFlag > 0)) :
                        aLocToNavd ( a424Row, addnHndl)  
                        aGSToNavd ( a424Row, addnHndl)  
                    #
                    if not (t424Row[13] == '' ) :
                      #tbd: Search x810 rowCode 6 for GS entry
                      compGS(a424Row )   
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
            a424Row = cur.fetchone()
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
  else :
    if (compType == 'loc') :
      listPFId  = "./loc-mismatch.txt"
      listPFId  = "./loc-list.txt"
      addnPFId  = "./loc-nav.dat"
      a424Table = 'loc_navaid'
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
