import os
from subprocess import call

def metamapStarter():
    # Intro loading of metamap and etc.
    os.chdir('/Users/bholmes/public_mm')
    call(["bin/skrmedpostctl", "start"])
    call(["bin/wsdserverctl", "start"])

def metamapCloser():
    call(["bin/skrmedpostctl", "stop"])
    call(["bin/wsdserverctl", "stop"])
