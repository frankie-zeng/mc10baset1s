import subprocess
import os
import re


app=os.path.join(os.path.dirname(__file__),'9500eepApp.exe')
genCmd=[app]

def readPhyReg(addr):
    output=subprocess.run([app,'-y',hex(addr)],capture_output=True)
    ret=output.stdout
    find=re.findall(r"Register (.*)\\r\\n",str(ret))
    regVal=find[0].split(':')
    return int(regVal[1],16)
    

   
def writePhyReg(addr,val):
    print(hex(val))
    subprocess.run([app,'-Y',hex(addr),'-v',hex(val)],capture_output=True)
    

def readGenReg(addr):
    output=subprocess.run([app,'-R',hex(addr)],capture_output=True)
    ret=output.stdout
    find=re.findall(r"Register (.*)\\r\\n",str(ret))
    regVal=find[0].split(':')
    return int(regVal[1],16)


def writeGenReg(addr,val):
    print(hex(val))
    subprocess.run([app,'-W',hex(addr),'-v',hex(val)],capture_output=True)



# writeGenReg(0x24,0x771)
# print(readGenReg(0x100))


def ledCtrl(index,on):
    if index<3:
        val=readGenReg(0x24)
        val|=0x770
        if on:
            val&=~(1<<index)
        else:
            val|=1<<index
        writeGenReg(0x24,val)
# ledCtrl(2,False)
# ledCtrl(1,False)
# ledCtrl(0,False)
ledCtrl(0,True)