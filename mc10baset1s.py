import subprocess
import os
import re


app=os.path.join(os.path.dirname(__file__),'9500eepApp.exe')
genCmd=[app]

def readPhyReg(addr):
    output=subprocess.run([app,'-y',str(addr)],capture_output=True)
    ret=output.stdout
    find=re.findall(r"Register (.*)\\r\\n",str(ret))
    regVal=find[0].split(':')
    return int(regVal[1],16)
    

   
def writePhyReg(addr,val):
    subprocess.run([app,'-Y',str(addr),'-v',str(val)],capture_output=True)
    

def readGenReg(addr):
    output=subprocess.run([app,'-R',str(addr)],capture_output=True)
    ret=output.stdout
    find=re.findall(r"Register (.*)\\r\\n",str(ret))
    regVal=find[0].split(':')
    return int(regVal[1],16)

writePhyReg(0,0x800)
print(readPhyReg(1))