import numpy as np
import struct, math
import xml.etree.ElementTree as ET
import os.path

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
    def __init__(self, xml, fps = 24, startFrame = 1, endFrame = 200, channels = ['Shape',], cacheFormat = 'mcc', cacheType = 'OneFilePerFrame'):
        self._fps = int(fps)
        self._xml = xml
        self._startFrame = int(startFrame)
        self._endFrame = int(endFrame)
        self._channels = channels
        self._format = cacheFormat
        self._type = cacheType
        self._channelTypes = []

    def read(self):
        self.tree = ET.ElementTree(file = self._xml)
        tree = ET.ElementTree(file = self._xml)
        root = tree.getroot()
        timePerFrame = 250

        for child in root.findall('cacheTimePerFrame'):
            timePerFrame = int(float(child.attrib['TimePerFrame']))
            self._fps = int(6000/timePerFrame)

        for child in root.findall('time'):
            timeRange = '-'.join(child.attrib['Range'].split('-')[0:-1]), child.attrib['Range'].split('-')[-1]
            self._startFrame = int(float(timeRange[0])/timePerFrame)
            self._endFrame = int(float(timeRange[1])/timePerFrame)

        for child in root.findall('cacheType'):
            self._format = child.attrib['Format']

        for child in root.findall('cacheType'):
            self._type = child.attrib['Type']

        self._channels = []

        for em in root.findall('Channels'):
            for child in em:
                self._channels.append(child.attrib['ChannelName'])

        self._channelTypes = []

        for em in root.findall('Channels'):
            for child in em:
                self._channelTypes.append(child.attrib['ChannelType'])

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

        if self._channelTypes == []:
            self._channelTypes = ['FloatVectorArray']*len(self._channels)  # Defaul Channel Type

        i = 0
        for ch in self._channels:
            self._xml_str += '<channel'+str(i)+' ChannelName="'+self._channels[i]+'" ChannelType="'+self._channelTypes[i]+'" ChannelInterpretation="positions" SamplingType="Regular" SamplingRate="'+str(int(timePerFrame))+'" StartTime="'+str(int(self._startFrame*timePerFrame))+'" EndTime="'+str(int(self._endFrame*timePerFrame))+'"/>\n'
            i += 1

        self._xml_str += '</Channels>\n\
        </Autodesk_Cache_File>'

    def getXMLString(self):
        self._genXMLString()
        return self._xml_str

    def getChannels(self):
        return self._channels

    def setChannels(self,ch):
        if type(ch) is list:
            self._channels = ch

    def getChannelTypes(self):
        return self._channelTypes

    def setChannelTypes(self, ch_types):
        if type(ch_type) is list:
            self._channelTypes = ch_types

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

    def __init__(self, xml_path, frame = 1, channels = ['Shape',], pointsArray = [[[0,0,0],],]):
        self.__mcc_head_unpack_string = '>4sL8sLl4sLl4sLl'
        self.__mcx_head_unpack_string = '>4sLQ8sLQ2L4sLQ2l4slQ2l'
        self._xmlpath = xml_path
        xml = NCacheXML(self._xmlpath)
        if os.path.exists(xml_path):
            xml.read()
        self._type = xml.getType()
        self._format = xml.getFormat()
        self._channelTypes = xml.getChannelTypes()
        self._xml = xml

        self._step = xml.getStep()
        self._frame = frame
        self.__genPath()
        self.__genHead()
        self._channels = channels
        self._pointsArray = pointsArray
        self._p_amount = 0
        
        for i in pointsArray:
            self._p_amount += np.array(i).size/3        

    def read(self):
        self.__genPath()
        file = open(self._path, 'rb')
        xml = NCacheXML(self._xmlpath)

        if os.path.exists(self._xmlpath):
            xml.read()

        self._xml = xml
        self._format = xml.getFormat()
        self._channels = xml.getChannels()
        self._channelTypes = xml.getChannelTypes()

        if self._format == 'mcc':
            self._head = file.read(48)
            head = struct.unpack(self.__mcc_head_unpack_string, self._head)
            block = struct.unpack('>4sL4s', file.read(12))
            blockDataLength = block[1]
        else:
            self._head = file.read(92)
            head = struct.unpack(self.__mcx_head_unpack_string, self._head)
            block = struct.unpack('>4sLQ4s', file.read(20))
            blockDataLength = block[2]
        
        self._pointsArray = []

        self._p_amount = 0

        if self._format == 'mcc':
            step = 60
            for i in range(len(self._channels)):
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
            for i in range(len(self._channels)):
                temp = struct.unpack('>4sLQ', file.read(16))
                name_length = int(math.ceil(float(temp[2])/8)*8)
                temp = struct.unpack('>'+str(name_length)+'s', file.read(name_length))
                temp = struct.unpack('>4sLQ2L4sLQ', file.read(40))
                step_push = int(math.ceil(float(temp[7])/8)*8)
                step += 16+name_length+40+step_push

                if temp[5] == 'FVCA':
                    self._p_amount += temp[7]/12
                    pos = struct.unpack('>'+str(temp[3]*3)+'f', file.read(temp[7]))
                    self._pointsArray.append(np.array(pos, dtype=np.float32).reshape(-1,3).tolist())
                elif temp[5] == 'DVCA':
                    self._p_amount += temp[7]/24
                    pos = struct.unpack('>'+str(temp[3]*3)+'d', file.read(temp[7]))
                    self._pointsArray.append(np.array(pos, dtype=np.float64).reshape(-1,3).tolist())

                file.seek(step)
        file.close()

    def write(self):
        self.__genPath()
        self.__genHead()

        with open(self._path,'wb') as f:

            f.write(self._head)

            tempNameLength = 0
            self._p_amount = self.getAmount()

            for ch in self._channels:    
                tempNameLength += self.__genNameLength(ch)

            block = ''

            if self._format == 'mcc':
                amount_size = 0
                for n,i in enumerate(self._pointsArray[:]):
                    if self._channelTypes[n] == 'FloatVectorArray':
                        amount_size += len(i)
                    elif self._channelTypes[n] == 'DoubleVectorArray':
                        amount_size += len(i)*2

                block = struct.pack('>4sL4s','FOR4',amount_size*12+28*len(self._channels)+12+tempNameLength-8,'MYCH')
            else:
                amount_size = 0
                amout_push = 0
                for n,i in enumerate(self._pointsArray[:]):
                    if self._channelTypes[n] == 'FloatVectorArray':
                        amount_size += len(i)
                        if (len(i)*3*4) % 8 != 0:
                            amout_push += 1
                    elif self._channelTypes[n] == 'DoubleVectorArray':
                        amount_size += len(i)*2

                block = struct.pack('>4sLQ4s','FOR8',0,amount_size*12+56*len(self._channels)+20+tempNameLength-16+amout_push*4,'MYCH')

            f.write(block)

            if self._channelTypes == []:
                self._channelTypes = ['FloatVectorArray'] * len(self._channels)

            for i,ch in enumerate(self._channels):
                pointsArray = [] 
                if self._channelTypes[i] == 'FloatVectorArray':
                    pointsArray = np.array(self._pointsArray[i], dtype = np.float32)
                elif self._channelTypes[i] == 'DoubleVectorArray':
                    pointsArray = np.array(self._pointsArray[i], dtype = np.float64)

                p_amount = len(pointsArray)

                tempNameLength = self.__genNameLength(ch)

                data = ''

                if self._format == 'mcc':
                    if self._channelTypes[i] == 'FloatVectorArray':
                        data = struct.pack('>4sL'+str(tempNameLength)+'s4s2L4sl','CHNM',len(ch)+1,ch,'SIZE',4,p_amount,'FVCA',p_amount*12)
                    elif self._channelTypes[i] == 'DoubleVectorArray':
                        data = struct.pack('>4sL'+str(tempNameLength)+'s4s2L4sl','CHNM',len(ch)+1,ch,'SIZE',4,p_amount,'DVCA',p_amount*24)
                else:
                    if self._channelTypes[i] == 'FloatVectorArray':
                        data = struct.pack('>4sLQ'+str(tempNameLength)+'s4sLQ2L4sLQ','CHNM',0,len(ch)+1,ch,'SIZE',0,4,p_amount,0,'FVCA',0,p_amount*12)
                    elif self._channelTypes[i] == 'DoubleVectorArray':  
                        data = struct.pack('>4sLQ'+str(tempNameLength)+'s4sLQ2L4sLQ','CHNM',0,len(ch)+1,ch,'SIZE',0,4,p_amount,0,'DVCA',0,p_amount*24)

                f.write(data)

                if self._channelTypes[i] == 'FloatVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f4').tostring())
                elif self._channelTypes[i] == 'DoubleVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f8').tostring())

                if self._format == 'mcx':
                    if self._channelTypes[i] == 'FloatVectorArray':
                        if (p_amount*3*4) % 8 != 0:
                            f.write(struct.pack('>L',0))

            f.flush()

    def getChannels(self):
        return self._channels

    def setChannels(self, channels):
        self._channels = channels

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
        self.__genPath()
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

    def __genNameLength(self, ch):
        tempNameLength = ''
        if self._format == 'mcc':
            tempNameLength = (len(ch)+4-(len(ch)%4)) if len(ch)%4 else len(ch)+4
        else:
            tempNameLength = (len(ch)+8-(len(ch)%8)) if len(ch)%8 else len(ch)+8
        return tempNameLength

    def __genHead(self):
        if self._format == 'mcc':
            self._head = struct.pack(self.__mcc_head_unpack_string,'FOR4',40,'CACHVRSN',4,808333568,'STIM',4,self._step*self._frame,'ETIM',4,self._step*self._frame)
        elif self._format == 'mcx':
            self._head = struct.pack(self.__mcx_head_unpack_string,'FOR8',0,76,'CACHVRSN',0,4,808333568,0,'STIM',0,4,self._step*self._frame,0,'ETIM',0,4,self._step*self._frame,0)
        else:
            return

    def __genPath(self):
        if self._format == 'mcc':
            self._path = self._xmlpath.replace('.xml','Frame'+str(self._frame)+'.mc')
        elif self._format == 'mcx':
            self._path = self._xmlpath.replace('.xml','Frame'+str(self._frame)+'.mcx')
        else:
            return

class NPCacheMC(NCacheMC, object):
    def __init__(self, xml_path, frame = 1, channels = ['Shape',], pointsArray = [[[0,0,0],],]):
        super(NPCacheMC,self).__init__(xml_path, frame = frame, channels = channels, pointsArray = pointsArray)

if __name__ == '__main__':
    path = ['D:/temp/ncache/p32.xml', 'D:/temp/ncache/p32d.xml', 'D:/temp/ncache/p64.xml', 'D:/temp/ncache/p64d.xml']
    for xml in path:
        print xml
        x = NCacheXML(xml)
        x.read()
        print x.getStartFrame(), x.getEndFrame(), x.getChannels()


    for xml in path:
        print xml, 'mcc'
        for i in range(-9,2):
            mc = NCacheMC(xml_path = xml)
            mc.setFrame(frame = i)
            mc.read()
            print mc.getChannels()
            mc.write()
