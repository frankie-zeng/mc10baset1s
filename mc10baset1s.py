# -*- coding: UTF-8 -*-
import argparse
import subprocess
import os
import re
if os.name!='nt':
    import usb.core
    import usb.util
    import struct









class winAction():
    def __init__(self):
        self.app=os.path.join(os.path.dirname(__file__),'9500eepApp.exe')
        

    def attachDevice(self):
        output=subprocess.run([self.app,'-G','o'],capture_output=True)
        if output.returncode !=0:
            return False
        else:
            return True


    def readPhyReg(self,addr):
        output=subprocess.run([self.app,'-y',hex(addr)],capture_output=True)
        ret=output.stdout
        find=re.findall(r"Register (.*)\\r\\n",str(ret))
        regVal=find[0].split(':')
        return int(regVal[1],16)
        

    
    def writePhyReg(self,addr,val):
        subprocess.run([self.app,'-Y',hex(addr),'-v',hex(val)],capture_output=True)
        

    def readGenReg(self,addr):
        output=subprocess.run([self.app,'-R',hex(addr)],capture_output=True)
        ret=output.stdout
        find=re.findall(r"Register (.*)\\r\\n",str(ret))
        regVal=find[0].split(':')
        return int(regVal[1],16)


    def writeGenReg(self,addr,val):
        subprocess.run([self.app,'-W',hex(addr),'-v',hex(val)],capture_output=True)

class LinuxAction():
    def __init__(self):
        import usb.core
        import usb.util
    def attachDevice(self):
        self.dev = usb.core.find(idVendor=0x0424, idProduct=0x9e00)
        if self.dev is None:
            return False
        else:
            return True
    def readGenReg(self,addr):
        ret=self.dev.ctrl_transfer(0xC0, 0xa1, 0, addr, 4)
        val=struct.unpack('<I',ret)[0]
        return val
    def writeGenReg(self,addr,val):
        wLengthData=struct.pack('<I',val)
        self.dev.ctrl_transfer(0x40, 0xa0, 0, addr, wLengthData)
    def readPhyReg(self,addr):
        phyAddr=7
        val=phyAddr<<11|addr<<6
        self.writeGenReg(0x114,val)
        while self.readGenReg(0x114)&0x1:
            pass
        return self.readGenReg(0x118)
    def writePhyReg(self,addr,data):
        self.writeGenReg(0x118,data)
        phyAddr=7
        val=phyAddr<<11|addr<<6|2
        self.writeGenReg(0x114,val)
        while self.readGenReg(0x114)&0x1:
            pass



class mc10baset1s():
    def __init__(self):
        if os.name=='nt':
            self.action= winAction()
        else:
            self.action = LinuxAction()
        self.attached=self.action.attachDevice()
        if self.attached == False:
            raise "Couldn't found device"
      
    def writePhyReg(self,addr,val):
        self.action.writePhyReg(addr,val)

    def writeGenReg(self,addr,val):
        self.action.writeGenReg(addr,val)

    def readPhyReg(self,addr):
        return self.action.readPhyReg(addr)

    def readGenReg(self,addr):
        return self.action.readGenReg(addr)

    def readMMDreg(self,index,addr):
        #write address
        data=0<<14|index
        self.writePhyReg(0x0d,data)
        self.writePhyReg(0x0e,addr)
        #read 
        data=1<<14|index
        self.writePhyReg(0x0d,data)
        return self.readPhyReg(0x0e)

    def writeMMDreg(self,index,addr,val):
        #write address
        data=0<<14|index
        self.writePhyReg(0x0d,data)
        self.writePhyReg(0x0e,addr)
        #read 
        data=1<<14|index
        self.writePhyReg(0x0d,data)
        self.writePhyReg(0x0e,val)
    
    def ledCtrl(self,index,on):
        if index<3:
            val=self.readGenReg(0x24)
            val&=0xfff
            val|=0x770
            if on:
                val&=~(1<<index)
            else:
                val|=1<<index
            self.writeGenReg(0x24,val)

    def readPhyId(self):
        id=[]
        id.append(hex(self.readPhyReg(0x2)))
        id.append(hex(self.readPhyReg(0x3)))
        return id


    #mmd1
    def setT1sTestMode(self,mode):
        self.writeMMDreg(1,0x8fb,(mode<<13)&0xe000)

    def getT1sTestMode(self):
        return self.readMMDreg(1,0x8fb)>>13

    #mmd3
    def getStatus1(self):
        return self.readMMDreg(0x1f,0x0018)
    def getStatus2(self):
        return self.readMMDreg(0x1f,0x0019)
    def getStatus3(self):
        return self.readMMDreg(0x1f,0x001a)


    def getRmtJabCnt(self):
        return self.readMMDreg(3,0x08F5)
    def getCorTxCnt(self):
        return self.readMMDreg(3,0x08F6)   

    #mmd0x1f




    def readBeaconCnt(self):
        low=self.readMMDreg(0x1f,0x27)
        high=self.readMMDreg(0x1f,0x26)
        return (high*0x10000+low)
    def readTransmitOppoCnt(self):
        low=self.readMMDreg(0x1f,0x25)
        high=self.readMMDreg(0x1f,0x24)
        return (high*0x10000+low)
    def plcaCtrl(self,enable,nodeCnt,nodeId,timer,burst):
        self.writeMMDreg(0x1f,0xCA02,nodeCnt<<8|nodeId)
        if enable:
            self.writeMMDreg(0x1f,0xCA01,0x8000)
        else:
            self.writeMMDreg(0x1f,0xCA01,0)   
        self.writeMMDreg(0x1f,0xCA04,timer&0xff)
        self.writeMMDreg(0x1f,0xCA05,burst&0xff) 
    def getPLCAStatus(self):
        return self.readMMDreg(0x1f,0xCA03)
    def getPLCATotmr(self):
        return self.readMMDreg(0x1f,0xCA04)
    def getPLCABurst(self):
        return self.readMMDreg(0x1f,0xCA05)
    def readPCSFault(self):
        val=self.readPhyReg(0x08F4)
        if val&0x80:
            return True
        else:
            return False
    def readRemoteJabberCnt(self):
        return self.readPhyReg(0x08f5)
    def readCorruptedTransmitCnt(self):
        return self.readPhyReg(0x08f6)
    
    

# writeGenReg(0x24,0x771)
# print(readGenReg(0x100))





mc = mc10baset1s()

def parse_args():

    parser = argparse.ArgumentParser()

    plca = parser.add_subparsers()
    plcaParser= plca.add_parser('plca',help='Set PLCA param')
    plcaParser.add_argument('--enable',action='store_const', const=True,help='enable or disable PLCA')
    plcaParser.add_argument('--nodeId',help='PLCA node ID',type=int, default=0)
    plcaParser.add_argument('--nodeCnt',help='PLCA node count',default=2,type=int)
    plcaParser.add_argument('--timer',help='PLCA transmit opportunity timer, default is 32(100ns)', default=32, type=int)
    plcaParser.add_argument('--burst',help='PLCA maximum burst count', default=0, type=int)

    statusParser = plca.add_parser('status',help='Display system status')
    statusParser.add_argument('--plca', action='store_const', const=True, help='Get PLCA status')
    statusParser.add_argument('--pcs', action='store_const', const=True, help='Get PCS status')
    

    statusParser = plca.add_parser('led',help='Onboard LED control')
    statusParser.add_argument('--led1',  choices=['on','off'])
    statusParser.add_argument('--led2',  choices=['on','off'])
    statusParser.add_argument('--led3',  choices=['on','off'])

    parser.add_argument('--reset','-r',action='store_const', const=True,help='Reset the PHY')

    args = parser.parse_args()
    return args
# app = Flask(__name__)

if __name__ == '__main__':
    args = parse_args()
    if args.reset:
        mc.writePhyReg(0,0x8000)
    else:
        #plca
        if 'nodeId' in args:
            mc.plcaCtrl(args.enable,args.nodeCnt,args.nodeId,args.timer,args.burst)
        #status
        if 'plca' in args:
            if args.plca!=None:
                status1=mc.getStatus1()
                status3=mc.getStatus3()
                burst=mc.getPLCABurst()
                print('PLCA status:')
                print('Transmit Collision Status (TXCOL): %d' % (bool(status1&0x400)))
                print('Transmit Jabber Status (TXJAB): %d' % (bool(status1&0x200)))
                print('PLCA Empty Cycle Status (EMPCYC): %d' % (bool(status1&0x80)))
                print('Receive in Transmit Opportunity (RXINTO): %d' % (bool(status1&0x40)))
                print('Unexpected BEACON Received (UNEXPB): %d' % (bool(status1&0x20)))
                print('BEACON Received Before Transmit Opportunity (BCNBFTO): %d' % (bool(status1&0x10)))
                print('PLCA Symbols Detected (PLCASYM): %d' % (bool(status1&0x4)))
                print('End-of-Stream Delimiter Error (ESDERR): %d' % (bool(status1&0x2)))
                print('5B Decode Error (DEC5B): %d' % (bool(status1&0x1)))
                print('PLCA Error Transmit Opportunity ID (ERRTOID): %d' % ((status3&0xff)))
                print('Transmit Opportunity Count (TOCNT): %ld' % (mc.readTransmitOppoCnt()))
                print('Beacon Count (BCNCNT): %ld' % (mc.readBeaconCnt()))
            if args.pcs!=None:
                print('PCS status:')
                fault=mc.readPCSFault()
                print('PCS Fault Indication: %d' % (fault))
                print('Remote Jabber Count (RMTJABCNT): %d' % (mc.readRemoteJabberCnt()))
                print('Corrupted Transmit Count (CORTXCNT): %d' % (mc.readCorruptedTransmitCnt()))
        #led
        if 'led1' in args:
            if args.led1!=None:
                if args.led1 == 'on':
                    mc.ledCtrl(0,True)
                else:
                    mc.ledCtrl(0,False)
            if args.led2!=None:
                if args.led2 == 'on':
                    mc.ledCtrl(1,True)
                else:
                    mc.ledCtrl(1,False)
            if args.led3!=None:
                if args.led3 == 'on':
                    mc.ledCtrl(2,True)
                else:
                    mc.ledCtrl(2,False)