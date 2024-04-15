psycoNavdat
  
  A derivation of https://pypi.org/project/psycopg2
  
                                                                   
  Python scripts for exploring and comparing ARINC424 and Flighgear Navigation 
    postgresql databases.
     
  For generating ARINC424   database see: https://github.com/robertjkeller/PyARINC424
  For generating Flightgear database see: https://github.com/bitwisetech/pyNavdat
  
  To use these scripts, install psycopg2: https://pypi.org/project/psycopg2/
    and copy these scripts into psycopg2/env folder
     
  compLocs.py     compares localizer entries in ARINC424 with Flightgear's XP810 database
  compNavaids.py  compares vhf / ndb entries in ARINC424 with Flightgear's XP810 database
    Custom overlay nav.dat and summary lists are output
   
  genrAirpXmls,py generates airport runway threshold.xml and ils.xml files from ARINC424 database
  
  Use python progname.py --help for more details
     
