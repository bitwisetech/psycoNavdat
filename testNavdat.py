#!/usr/bin/env python

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
  
def a424ToNavdat ( t424Row, navdatHndl) :
  aSect = t424Row[2]
  aSubs = t424Row[3]
  aClas = t424Row[10]
  if (aSect == 'D') :
    if not (t424Row[11] == '' ) :
      navdLati = ( "%-02.8f" % (deciLati( t424Row[11]))).rjust(12, ' ')
    if not (t424Row[12] == '' ) :
      navdLong = ( "%-03.8f" % (deciLong( t424Row[12]))).rjust(13, ' ')
    navdDecl = ( "%6i"  % magnDecl(t424Row[16])).rjust( 6, ' ')
    if (t424Row[17] == '') :
      navdElev = ( "%s"  % (t424Row[17].rjust( 6, ' ')))
    else :  
      navdElev = ( "     0")
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
      if addNavd :  
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
        if addNavd :  
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
          if addNavd :  
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
        if addNavd :  
          addnHndl.write( navdLine)
  #   

NDBLine    = ('S', 'USA', 'D', 'B', '', '', 'AAA', 'K5', '0', '03290', 'H MW', 'N40093642', 'W089201686', 'E0000', 'NAR', 'ABRAHAM', '26455', '1703')
VORLine    = ('S', 'USA', 'D', '', '', '', 'ALI', 'K4', '0', '11450', 'V LW', 'N27442328', 'W098011683', '', '', '', 'E0060', '', '1', '', '', 'NAR', 'ALICE', '24571', '1703')
VORDMELine = ('S', 'USA', 'D',  '', '', '', 'ABR', 'K3', '0', '11300', 'VDH',  'N45250248', 'W098220739', '',    'N45250248', 'W098220739', 'E0070', '01303', '2', '', '', 'NAR', 'ABERDEEN', '24551', '2110')
VORTACLine = ('S', 'USA', 'D',  '', '', '', 'ALS', 'K2', '0', '11390', 'VTHW', 'N37205697', 'W105485592', '',    'N37205697', 'W105485592', 'E0130', '07535', '2', '', '', 'NAR', 'ALAMOSA', '24573', '1907')
TACANLine  = ('S', 'USA', 'D',  '', '', '', 'BAB', 'K2', '0', '10860', ' TLW', '',          '',           'BAB', 'N39080526', 'W121262673', 'E0160', '00089', '1', '', '', 'NAR', 'BEALE', '24597', '2401')  
DMELine    = ('S', 'CAN', 'D', '', '', '', 'YOW', 'CY', '0', '11460', ' DUW', '', '', 'YOW', 'N45263013', 'W075534896', 'W0140', '00450', '3', '', '', 'NAR', 'OTTAWA', '00306', '2401')
 
verbose = 1
addNavd = 0
a424ToNavdat ( NDBLine, '')
a424ToNavdat ( VORLine, '')
a424ToNavdat ( VORDMELine, '')
a424ToNavdat ( VORTACLine, '')
a424ToNavdat ( TACANLine, '')
a424ToNavdat ( DMELine, '')
