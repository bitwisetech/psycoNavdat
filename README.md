    
 ./qAirpRwys.py : Flightgear threshold, ils .xml files from CIFS database
                                                                   
Prerequ: Install PyARINC424 and build the ARINC242 postsegrsql database  
  ref:  https://github.com/robertjkeller/PyARINC424  
                                                                   
         Install and configure psycopg2 Python database adapter  
  ref:  https://pypi.org/project/psycopg2/  
    ( For Fedora39 the binary -bin package was used   
                                                                    
  Copy these scripts into psycopg2/env folder and execute from there  
  Create a folder: psycopgs/env/Airports as a default output folder 
                                                                    
 ./qAirpRwys.py : Options: 
   -a --airport [ ICAO for single airport 
          e.g ./qAirpRwys.py -a KATL
   -h --help    Print this help
   -m --multiPass Create multiple entries from spec file 
          use default specList.txt or -s to specify 
   -o --outpPath [somePath ]  Specify Pathname for output ( no TrailSlash, noFileId ) 
          e.g    ./qAirpRwys.py -a KATL -o ~/Airports 
   -s --specfile [PAth/FileID] List of Airport ICAO names for processing 
          INFO: message is output for airport has not a single entry in database 
   -t --tree  Use a pre-created folder tree , like terrasync/Airports 
          (Hint To create an empty tree: copy terrasync/Airports entirely,  
           and then, with care, use rsync -r --remove-source-files newTree ./dump 
           then delete ./dump leaving an empty tree structure in newTree
                                                                    
   -v --verbose Outputs console printouts in addition to writing xml 
                                                                    
   Python scripts: qAirp.py, qAlft.py, qLocs.py, qRwys.py           
          are for exploring the database, use -a ICAO for console   
          output of single database queries                    
