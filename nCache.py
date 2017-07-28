import numpy as np
import struct, math
import xml.etree.ElementTree as ET
import os.path
import threading

def removeNamespace(name, ns = ''):
    temp_name = name.split('|')
    fixed_name = []
    for name in temp_name:
        if ns == '':
            fixed_name.append(name.split(':')[-1])
        else:
            fixed_name.append(":".join([x for x in name.split(':') if x != ns]))
    fixed_name = '|'.join(fixed_name)

    return fixed_name

def removeObjsNamespace(objs, nspace = ''):
    fixed = []
    for obj in objs:
        fixed.append(removeNamespace(obj, ns = nspace))
    return fixed

def removeObjNamespace(objs, target_obj, nspace = ''):
    fixed = []
    for obj in objs:
        if obj == target_obj:
            fixed.append(removeNamespace(obj, ns = nspace))
        else:
            fixed.append(obj)
    return fixed

def backwardObj(objs, step):
    step = int(step)
    fixed = []
    if step > 0:
        for obj in objs:
            temp_name = obj.split('|')
            if len(temp_name) < (step+1):
                fixed.append(temp_name[-1])
            else:
                fixed.append("|".join(temp_name[step:]))
        return fixed
    else:
        return objs

class NCacheXML:
    def __init__(self, xml, fps = 24, startFrame = 1, endFrame = 200, channel = ['Shape',], cacheFormat = 'mcc', cacheType = 'OneFilePerFrame'):
        self._fps = int(fps)
        self._xml = xml
        self._startFrame = int(startFrame)
        self._endFrame = int(endFrame)
        self._channel = channel
        self._format = cacheFormat
        self._type = cacheType
        self._channelType = []

    def read(self):
        self.tree = ET.ElementTree(file = self._xml)
        tree = ET.ElementTree(file = self._xml)
        root = tree.getroot()
        timePerFrame = 250

        for child in root.findall('cacheTimePerFrame'):
            timePerFrame = int(float(child.attrib['TimePerFrame']))
            self._fps = int(6000/timePerFrame)

        for child in root.findall('time'):
            timeRange = child.attrib['Range'].split('-')
            self._startFrame = int(float(timeRange[0])/timePerFrame)
            self._endFrame = int(float(timeRange[1])/timePerFrame)

        for child in root.findall('cacheType'):
            self._format = child.attrib['Format']

        for child in root.findall('cacheType'):
            self._type = child.attrib['Type']

        self._channel = []

        for em in root.findall('Channels'):
            for child in em:
                self._channel.append(child.attrib['ChannelName'])

        self._channelType = []

        for em in root.findall('Channels'):
            for child in em:
                self._channelType.append(child.attrib['ChannelType'])

    def write(self):
        with open(self._xml,'wb') as f:
        
            self._genXMLString()

            root = ET.fromstring(self._xml_str)
            
            f.write(ET.tostring(root))
            

    def setFps(self, fps):
        self._fps = int(fps)

    def getFps(self):
        return self._fps

    def setStartFrame(self, startFrame):
        self._startFrame =int(startFrame)

    def getStartFrame(self):
        return self._startFrame

    def setEndFrame(self, endFrame):
        self._endFrame = int(endFrame)

    def getEndFrame(self):
        return self._endFrame

    def _genXMLString(self):

        timePerFrame = int(6000/self._fps)
        cacheType = self._type

        self._xml_str = '<?xml version="1.0"?>\n\
        <Autodesk_Cache_File>\n\
            <cacheType Type="'+cacheType+'" Format="'+self._format+'"/>\n\
            <time Range="'+str(int(self._startFrame*timePerFrame))+'-'+str(int(self._endFrame*timePerFrame))+'"/>\n\
            <cacheTimePerFrame TimePerFrame="'+str(int(timePerFrame))+'"/>\n\
            <cacheVersion Version="2.0"/>\n\
            <Channels>\n'

        if self._channelType == []:
            self._channelType = self._channelType + ['FloatVectorArray']*(len(self._channel)-len(self._channelType))

        i = 0
        for ch in self._channel:
            self._xml_str += '<channel'+str(i)+' ChannelName="'+self._channel[i]+'" ChannelType="'+self._channelType[i]+'" ChannelInterpretation="positions" SamplingType="Regular" SamplingRate="'+str(int(timePerFrame))+'" StartTime="'+str(int(self._startFrame*timePerFrame))+'" EndTime="'+str(int(self._endFrame*timePerFrame))+'"/>\n'
            i += 1

        self._xml_str += '</Channels>\n\
        </Autodesk_Cache_File>'

    def getXMLString(self):
        self._genXMLString()
        return self._xml_str

    def getChannels(self):
        return self._channel

    def setChannels(self,ch):
        if type(ch) is list:
            self._channel = ch

    def getChannelTypes(self):
        return self._channelType

    def setChannelTypes(self, ch_type):
        if type(ch_type) is list:
            self._channelType = ch_type

    def getFormat(self):
        return self._format

    def setFormat(self, fmt):
        self._format = fmt

    def getStep(self):
        return 6000/self._fps

    def getType(self):
        return self._type

    def setXMLPath(self, xml):
        self._xml = xml


class NCacheMC:

    def __init__(self, xml_path, frame = 1, channel = ['Shape',], pointsArray = [[[0,0,0],],]):
        self._xmlpath = xml_path
        xml = NCacheXML(self._xmlpath)
        if os.path.exists(xml_path):
            xml.read()
        self._type = xml.getType()
        self._format = xml.getFormat()
        self._xml = xml

        self._step = xml.getStep()
        self._frame = frame
        if self._format == 'mcc':
            self._path = xml_path.replace('.xml','Frame'+str(frame)+'.mc')
            self._head = struct.pack('>4sL8sLl4s2L4s2L','FOR4',40,'CACHVRSN',4,808333568,'STIM',4,self._step*frame,'ETIM',4,self._step*frame)
        else:
            self._path = xml_path.replace('.xml','Frame'+str(frame)+'.mcx')
            self._head = struct.pack('>4s3L8s5L4s5L4s5L','FOR8',0,0,76,'CACHVRSN',0,0,4,808333568,0,'STIM',0,0,4,self._step*frame,0,'ETIM',0,0,4,self._step*frame,0)
        self._channel = channel
        self._pointsArray = pointsArray
        self._p_amount = 0
        for i in pointsArray:
            self._p_amount += np.array(i).size/3        

    def read(self):
        file = open(self._path, 'rb')
        xml = NCacheXML(self._xmlpath)

        if os.path.exists(self._xmlpath):
            xml.read()

        self._xml = xml
        self._format = xml.getFormat()
        self._channel = xml.getChannels()
        self._chancelTypes = xml.getChannelTypes()

        if self._format == 'mcc':
            self._head = file.read(48)
            head = struct.unpack('>4sL8sLl4s2L4s2L', self._head)
            block = struct.unpack('>4sL4s', file.read(12))
            blockDataLength = block[1]
        else:
            self._head = file.read(92)
            head = struct.unpack('>4s3L8s5L4s5L4s5L', self._head)
            block = struct.unpack('>4s3L4s', file.read(20))
            blockDataLength = block[3]
        
        self._pointsArray = []

        self._p_amount = 0

        if self._format == 'mcc':
            step = 60
            for i in range(len(self._channel)):
                temp = struct.unpack('>4sL', file.read(8))
                name_length = int(math.ceil(float(temp[1])/4)*4)
                temp = struct.unpack('>'+str(name_length)+'s', file.read(name_length))
                temp = struct.unpack('>4s2L4sl', file.read(20))
                step += 8+name_length+20+temp[4]

                if temp[3] == 'FVCA':
                    self._p_amount += temp[4]/12
                    pos = struct.unpack('>'+str(temp[2]*3)+'f', file.read(temp[4]))
                    self._pointsArray.append(np.array(pos, dtype=np.float32).reshape(-1,3).tolist())
                elif temp[3] == 'DVCA':
                    self._p_amount += temp[4]/24
                    pos = struct.unpack('>'+str(temp[2]*3)+'d', file.read(temp[4]))
                    self._pointsArray.append(np.array(pos, dtype=np.float64).reshape(-1,3).tolist())

                file.seek(step)
        else:
            step = 112
            for i in range(len(self._channel)):
                temp = struct.unpack('>4s3L', file.read(16))
                name_length = int(math.ceil(float(temp[3])/8)*8)
                temp = struct.unpack('>'+str(name_length)+'s', file.read(name_length))
                temp = struct.unpack('>4s5L4s3L', file.read(40))
                step_push = int(math.ceil(float(temp[9])/8)*8)
                step += 16+name_length+40+step_push

                if temp[6] == 'FVCA':
                    self._p_amount += temp[9]/12
                    pos = struct.unpack('>'+str(temp[4]*3)+'f', file.read(temp[9]))
                    self._pointsArray.append(np.array(pos, dtype=np.float32).reshape(-1,3).tolist())
                elif temp[6] == 'DVCA':
                    self._p_amount += temp[9]/24
                    pos = struct.unpack('>'+str(temp[4]*3)+'d', file.read(temp[9]))
                    self._pointsArray.append(np.array(pos, dtype=np.float64).reshape(-1,3).tolist())

                file.seek(step)
        file.close()

    def write(self):

        if self._format == 'mcc':
            self._path = self._xmlpath.replace('.xml','Frame'+str(self._frame)+'.mc')
            self._head = struct.pack('>4sL8sLl4s2L4s2L','FOR4',40,'CACHVRSN',4,808333568,'STIM',4,self._step*self._frame,'ETIM',4,self._step*self._frame)
        elif self._format == 'mcx':
            self._path = self._xmlpath.replace('.xml','Frame'+str(self._frame)+'.mcx')
            self._head = struct.pack('>4s4s2L8s5L4s5L4s5L','FOR8','\xfe\x07\x00\x00',0,76,'CACHVRSN',0,0,4,808333568,0,'STIM',0,0,4,self._step*self._frame,0,'ETIM',0,0,4,self._step*self._frame,0)
        else:
            return

        with open(self._path,'wb') as f:

            f.write(self._head)

            tempNameLength = 0
            self._p_amount = self.getAmount()

            if self._format == 'mcc':
                for ch in self._channel:    
                    tempNameLength += (len(ch)+4-(len(ch)%4)) if len(ch)%4 else len(ch)+4
            else:
                for ch in self._channel:    
                    tempNameLength += (len(ch)+8-(len(ch)%8)) if len(ch)%8 else len(ch)+8

            block = ''

            if self._format == 'mcc':
                amount_size = 0
                for n,i in enumerate(self._pointsArray[:]):
                    temp = int(math.ceil(float(np.array(i).reshape(-1).size/3)/2)*2)
                    if self._chancelTypes[n] == 'FloatVectorArray':
                        temp = temp
                    elif self._chancelTypes[n] == 'DoubleVectorArray':
                        temp *= 2
                    amount_size += temp

                block = struct.pack('>4sL4s','FOR4',amount_size*12+28*len(self._channel)+12+tempNameLength-8,'MYCH')
            else:
                amount_size = 0
                for n,i in enumerate(self._pointsArray[:]):
                    temp = int(math.ceil(float(np.array(i).reshape(-1).size/3)/2)*2)
                    if self._chancelTypes[n] == 'FloatVectorArray':
                        temp = temp
                    elif self._chancelTypes[n] == 'DoubleVectorArray':
                        temp *= 2
                    amount_size += temp

                block = struct.pack('>4s3L4s','FOR8',0,0,amount_size*12+56*len(self._channel)+20+tempNameLength-16,'MYCH')

            f.write(block)

            i = 0

            for i,ch in enumerate(self._channel):
                pointsArray = [] 
                if self._chancelTypes[i] == 'FloatVectorArray':
                    pointsArray = np.array(self._pointsArray[i], dtype = np.float32)
                elif self._chancelTypes[i] == 'DoubleVectorArray':
                    pointsArray = np.array(self._pointsArray[i], dtype = np.float64)

                p_amount = len(pointsArray)

                if self._format == 'mcc':
                    tempNameLength = (len(ch)+4-(len(ch)%4)) if len(ch)%4 else len(ch)+4
                else:
                    tempNameLength = (len(ch)+8-(len(ch)%8)) if len(ch)%8 else len(ch)+8

                data = ''

                if self._format == 'mcc':
                    if self._chancelTypes[i] == 'FloatVectorArray':
                        data = struct.pack('>4sL'+str(tempNameLength)+'s4s2L4sl','CHNM',len(ch)+1,ch,'SIZE',4,p_amount,'FVCA',p_amount*12)
                    elif self._chancelTypes[i] == 'DoubleVectorArray':
                        data = struct.pack('>4sL'+str(tempNameLength)+'s4s2L4sl','CHNM',len(ch)+1,ch,'SIZE',4,p_amount,'DVCA',p_amount*24)
                else:
                    if self._chancelTypes[i] == 'FloatVectorArray':
                        data = struct.pack('>4s3L'+str(tempNameLength)+'s4s5L4s3L','CHNM',0,0,len(ch)+1,ch,'SIZE',0,0,4,p_amount,0,'FVCA',0,0,p_amount*12)
                    elif self._chancelTypes[i] == 'DoubleVectorArray':  
                        data = struct.pack('>4s3L'+str(tempNameLength)+'s4s5L4s3L','CHNM',0,0,len(ch)+1,ch,'SIZE',0,0,4,p_amount,0,'DVCA',0,0,p_amount*24)

                f.write(data)

                if self._chancelTypes[i] == 'FloatVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f4').tostring())
                elif self._chancelTypes[i] == 'DoubleVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f8').tostring())

                if self._format == 'mcx':
                    if self._chancelTypes[i] == 'FloatVectorArray':
                        if (p_amount*3*4) % 8 != 0:
                            f.write(struct.pack('>L',0))

                i += 1

            f.flush()

    def getChannel(self):
        return self._channel

    def setChannel(self, ch):
        self._channel = ch

    def getPointArray(self):
        return self._pointsArray

    def setPointArray(self, pArray):
        self._pointsArray = pArray

    def getAmount(self):
        self._p_amount = 0
        for i in self._pointsArray[:]:
            self._p_amount += np.array(i).reshape(-1).size
        self._p_amount /= 3
        return self._p_amount

    def getPath(self):
        return self._path

    def getStep(self):
        return self._frame * self._step

    def setFrame(self, frame):
        self._frame = int(frame)

    def getFrame(self):
        return self._frame

    def setXMLPath(self, xml_path):
        self._xmlpath = xml_path
        
    def setFormat(self, fmt):
        if fmt == 'mcc' or fmt == 'mcx':
            self._format = fmt
        if self._format == 'mcc' or self._format == 'mcx':
            return True
        else:
            return False

    def getFormat(self):
        return self._format

class NPCacheMC(NCacheMC, object):
    def __init__(self, xml_path, frame = 1, channel = ['Shape',], pointsArray = [[[0,0,0],],]):
        super(NPCacheMC,self).__init__(xml_path, frame = frame, channel = channel, pointsArray = pointsArray)

if __name__ == '__main__':
    path = 'D:/temp/ncache/double_p64.xml'
    xml = NCacheXML(path)
    print xml.getXMLString()
    xml.read()
    print xml.getXMLString()

    mc = NPCacheMC(xml_path = path)
    mc.setFrame(frame = 1)
    mc.read()
    print mc.getPointArray()
    print mc.getChannel()
    print mc.getAmount()

    mc.write()
