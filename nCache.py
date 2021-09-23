import math
import os.path
import struct
import xml.etree.ElementTree as ET

import numpy as np

'''
['DoubleArray', 'FloatVectorArray', 'DoubleVectorArray']
'''


# Please google: How Maya counts time
TICKS_PRE_SECOND = 6000


def removeNamespace(name, ns=''):
    temp_name = name.split('|')
    fixed_name = []
    for name in temp_name:
        if ns == '':
            fixed_name.append(name.split(':')[-1])
        else:
            fixed_name.append(
                ':'.join([x for x in name.split(':') if x != ns]))
    fixed_name = '|'.join(fixed_name)

    return fixed_name


def removeObjsNamespace(objs, nspace=''):
    fixed = []
    for obj in objs:
        fixed.append(removeNamespace(obj, ns=nspace))
    return fixed


def removeObjNamespace(objs, target_obj, nspace=''):
    fixed = []
    for obj in objs:
        if obj == target_obj:
            fixed.append(removeNamespace(obj, ns=nspace))
        else:
            fixed.append(obj)
    return fixed


def backwardObj(objs, step):
    step = int(step)
    fixed = []
    if step > 0:
        for obj in objs:
            temp_name = obj.split('|')
            if len(temp_name) < (step + 1):
                fixed.append(temp_name[-1])
            else:
                fixed.append('|'.join(temp_name[step:]))
        return fixed
    else:
        return objs


class NCacheXML(object):

    def __init__(self,
                 xml,
                 fps=24,
                 startFrame=1,
                 endFrame=200,
                 evalRate=1.0,
                 channels=None,
                 cacheFormat='mcc',
                 cacheType='OneFilePerFrame'):
        """"""
        channels = channels or ['Shape', ]

        if not xml.lower().endswith(".xml"):
            xml += ".xml"

        self._fps = int(fps)
        self._xml = xml
        self._startFrame = int(startFrame)
        self._endFrame = int(endFrame)
        self._evalRate = float(evalRate)
        self._channels = channels
        self._format = cacheFormat
        self._type = cacheType
        self._channelTypes = []
        self._channelInters = []

    def read(self):
        tree = ET.ElementTree(file=self._xml)
        root = tree.getroot()
        timePerFrame = 250

        for child in root.findall('cacheTimePerFrame'):
            timePerFrame = int(float(child.attrib['TimePerFrame']))
            self._fps = int(TICKS_PRE_SECOND / timePerFrame)

        for child in root.findall('time'):
            if len(child.attrib['Range'].split('-')) < 4:
                timeRange = (
                    '-'.join(child.attrib['Range'].split('-')[0:-1]),
                    child.attrib['Range'].split('-')[-1]
                )
            else:
                timeRange = (
                    '-'.join(child.attrib['Range'].split('-')[0:-2]),
                    '-'.join(child.attrib['Range'].split('-')[-2:])
                )

            self._startFrame = int(float(timeRange[0]) / timePerFrame)
            self._endFrame = int(float(timeRange[1]) / timePerFrame)

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

        for em in root.findall('Channels'):
            for child in em:
                self._channelInters.append(
                    child.attrib['ChannelInterpretation'])

    def write(self):
        self._genXMLString()
        with open(self._xml, 'wb') as f:
            root = ET.fromstring(self._xml_str)
            f.write(b'<?xml version="1.0"?>\n')
            f.write(ET.tostring(root))

    def setFps(self, fps):
        self._fps = int(fps)

    def getFps(self):
        return self._fps

    def setStartFrame(self, startFrame):
        self._startFrame = int(startFrame)

    def getStartFrame(self):
        return self._startFrame

    def setEndFrame(self, endFrame):
        self._endFrame = int(endFrame)

    def getEndFrame(self):
        return self._endFrame

    def setEvalRate(self, rate):
        self._evalRate = float(rate)

    def getEvalRate(self):
        return self._evalRate

    def __genChannelTypes(self):
        if not self._channelTypes:
            self._channelTypes = ['FloatVectorArray'] * len(self._channels)
        elif len(self._channelTypes) != len(self._channels):
            raise

    def __genChannelInters(self):
        if not self._channelInters:
            self._channelInters = ['positions'] * len(self._channels)
        elif len(self._channelInters) != len(self._channels):
            raise

    def _genXMLString(self):

        ticksPerFrame = self.getTicksPerFrame()
        cacheType = self._type

        self._xml_str = '''<Autodesk_Cache_File>
  <cacheType Type="{cacheType}" Format="{format}"/>
  <time Range="{startFrame}-{endFrame}"/>
  <cacheTimePerFrame TimePerFrame="{perFrame}"/>
  <cacheVersion Version="2.0"/>
  <Channels>\n'''.format(
            cacheType=cacheType,
            format=self._format,
            startFrame=int(self._startFrame * ticksPerFrame),
            endFrame=int(self._endFrame * ticksPerFrame),
            perFrame=int(ticksPerFrame),
        )

        self.__genChannelTypes()
        self.__genChannelInters()

        for i, ch in enumerate(self._channels):
            _ch_str = '    '  # indention
            _ch_str += ' '.join([
                '<channel%d' % i,
                'ChannelName="%s"' % self._channels[i],
                'ChannelType="%s"' % self._channelTypes[i],
                'ChannelInterpretation="%s"' % self._channelInters[i],
                'SamplingType="Regular"',
                'SamplingRate="%d"' % int(ticksPerFrame * self._evalRate),
                'StartTime="%d"' % int(self._startFrame * ticksPerFrame),
                'EndTime="%d"' % int(self._endFrame * ticksPerFrame),
                '/>\n'
            ])
            self._xml_str += _ch_str

        self._xml_str += '  </Channels>\n</Autodesk_Cache_File>'

    def getXMLString(self):
        self._genXMLString()
        return self._xml_str

    def getChannels(self):
        return self._channels

    def setChannels(self, ch):
        if type(ch) is list:
            self._channels = ch

    def getChannelTypes(self):
        return self._channelTypes

    def setChannelTypes(self, ch_types):
        if type(ch_types) is list:
            for chtype in ch_types:
                if self.__checkType(chtype) is False:
                    raise
            self._channelTypes = ch_types

    def getFormat(self):
        return self._format

    def setFormat(self, fmt):
        self._format = fmt

    def getTicksPerFrame(self):
        return int(TICKS_PRE_SECOND / self._fps)

    def getType(self):
        return self._type

    def setXMLPath(self, xml):
        self._xml = xml

    def getChannelInters(self):
        return self._channelInters

    def setChannelInters(self, chInters):
        self._channelInters = chInters

    def appendChannel(self, chName, chType='FloatVectorArray', chInter="positions"):
        if self.__checkType(chType):
            self._channels.append(chName)
            self._channelTypes.append(chType)
            self._channelInters.append(chInter)
        else:
            raise

    def __checkType(self, chType):
        types = ['DoubleArray', 'FloatVectorArray', 'DoubleVectorArray']
        if chType in types:
            return True
        else:
            return False


############################


class NCacheMC(object):
    """"""
    def __init__(self,
                 xml_path,
                 frame=1,
                 channels=None,
                 pointsArray=None):
        """"""
        channels = channels or ['Shape', ]
        pointsArray = pointsArray or [[[0, 0, 0], ], ]

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

        self._ticks_pre_frame = xml.getTicksPerFrame()
        self._frame = frame
        self.__genPath()
        self.__genHead()
        self._channels = channels
        self._pointsArray = pointsArray
        self._p_amount = 0
        self._ele_amounts = []

        for i in pointsArray:
            self._p_amount += np.array(i).size / 3

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
                try:
                    temp = struct.unpack('>4sL', file.read(8))
                except Exception:
                    return None

                name_length = int(math.ceil(float(temp[1]) / 4) * 4)
                # temp = struct.unpack(
                #     '>' + str(name_length) + 's', file.read(name_length))
                temp = struct.unpack('>4s2L4sl', file.read(20))
                step += 8 + name_length + 20 + temp[4]

                if temp[3] == 'FVCA':
                    self._ele_amounts.append(temp[4] / 12)
                    pos = struct.unpack(
                        '>' + str(temp[2] * 3) + 'f',
                        file.read(temp[4])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float32).reshape(-1, 3))

                elif temp[3] == 'DVCA':
                    self._ele_amounts.append(temp[4] / 24)
                    pos = struct.unpack(
                        '>' + str(temp[2] * 3) + 'd',
                        file.read(temp[4])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float64).reshape(-1, 3))

                elif temp[3] == 'DBLA':
                    self._ele_amounts.append(temp[4] / 8)
                    pos = struct.unpack(
                        '>' + str(temp[2]) + 'd',
                        file.read(temp[4])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float64).reshape(-1))

                file.seek(step)

            self._p_amount = sum(self._ele_amounts)

        else:
            step = 112
            for i in range(len(self._channels)):
                try:
                    temp = struct.unpack('>4sLQ', file.read(16))
                except Exception:
                    return None

                name_length = int(math.ceil(float(temp[2]) / 8) * 8)
                # temp = struct.unpack(
                #     '>' + str(name_length) + 's', file.read(name_length))
                temp = struct.unpack('>4sLQ2L4sLQ', file.read(40))
                step_push = int(math.ceil(float(temp[7]) / 8) * 8)
                step += 16 + name_length + 40 + step_push

                if temp[5] == 'FVCA':
                    self._ele_amounts.append(temp[7] / 12)
                    pos = struct.unpack(
                        '>' + str(temp[3] * 3) + 'f',
                        file.read(temp[7])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float32).reshape(-1, 3))

                elif temp[5] == 'DVCA':
                    self._ele_amounts.append(temp[7] / 24)
                    pos = struct.unpack(
                        '>' + str(temp[3] * 3) + 'd',
                        file.read(temp[7])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float64).reshape(-1, 3))

                elif temp[5] == 'DBLA':
                    self._ele_amounts.append(temp[7] / 8)
                    pos = struct.unpack(
                        '>' + str(temp[3]) + 'd',
                        file.read(temp[7])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float64).reshape(-1))

                file.seek(step)

            self._p_amount = sum(self._ele_amounts)

        file.close()
        return True

    def write(self):
        self.__genPath()
        self.__genHead()

        with open(self._path, 'wb') as f:

            f.write(self._head)

            tempNameLength = 0
            self._p_amount = self.getAmount()

            for ch in self._channels:
                tempNameLength += self.__genNameLength(ch)

            _ch_len = len(self._channels)

            if self._format == 'mcc':
                amount_size = 0
                for n, i in enumerate(self._pointsArray[:]):
                    if self._channelTypes[n] == 'FloatVectorArray':
                        amount_size += len(i) * 3
                    elif self._channelTypes[n] == 'DoubleVectorArray':
                        amount_size += len(i) * 2 * 3
                    elif self._channelTypes[n] == 'DoubleArray':
                        amount_size += len(i) * 2

                block = struct.pack(
                    '>4sL4s',
                    b'FOR4',
                    amount_size * 4 + 28 * _ch_len + 12 + tempNameLength - 8,
                    b'MYCH'
                )

            else:
                amount_size = 0
                amount_push = 0
                for n, i in enumerate(self._pointsArray[:]):
                    if self._channelTypes[n] == 'FloatVectorArray':
                        amount_size += len(i) * 3
                        if (len(i) * 3 * 4) % 8 != 0:
                            amount_push += 1
                    elif self._channelTypes[n] == 'DoubleVectorArray':
                        amount_size += len(i) * 2 * 3
                    elif self._channelTypes[n] == 'DoubleArray':
                        amount_size += len(i) * 3

                block = struct.pack(
                    '>4sLQ4s',
                    b'FOR8',
                    0,
                    amount_size * 4 + 56 * _ch_len + 20 + tempNameLength - 16
                    + amount_push * 4,
                    b'MYCH'
                )

            f.write(block)

            if not self._channelTypes:
                self._channelTypes = ['FloatVectorArray'] * len(self._channels)

            for i, ch in enumerate(self._channels):
                pointsArray = []
                if self._channelTypes[i] == 'FloatVectorArray':
                    pointsArray = self._pointsArray[i].astype(np.float32)
                elif self._channelTypes[i] == 'DoubleVectorArray':
                    pointsArray = self._pointsArray[i].astype(np.float64)
                elif self._channelTypes[i] == 'DoubleArray':
                    pointsArray = self._pointsArray[i].astype(np.float64)

                p_amount = len(pointsArray)

                tempNameLength = self.__genNameLength(ch)

                data = ''

                if self._format == 'mcc':

                    if self._channelTypes[i] == 'FloatVectorArray':
                        data = struct.pack(
                            '>4sL' + str(tempNameLength) + 's4s2L4sl',
                            b'CHNM',
                            len(ch) + 1,
                            str.encode(ch),
                            b'SIZE',
                            4,
                            p_amount,
                            b'FVCA',
                            p_amount * 12
                        )

                    elif self._channelTypes[i] == 'DoubleVectorArray':
                        data = struct.pack(
                            '>4sL' + str(tempNameLength) + 's4s2L4sl',
                            b'CHNM',
                            len(ch) + 1,
                            str.encode(ch),
                            b'SIZE',
                            4,
                            p_amount,
                            b'DVCA',
                            p_amount * 24
                        )

                    elif self._channelTypes[i] == 'DoubleArray':
                        data = struct.pack(
                            '>4sL' + str(tempNameLength) + 's4s2L4sl',
                            b'CHNM',
                            len(ch) + 1,
                            str.encode(ch),
                            b'SIZE',
                            4,
                            p_amount,
                            b'DBLA',
                            p_amount * 8
                        )

                else:
                    if self._channelTypes[i] == 'FloatVectorArray':
                        data = struct.pack(
                            '>4sLQ' + str(tempNameLength) + 's4sLQ2L4sLQ',
                            b'CHNM',
                            0,
                            len(ch) + 1,
                            str.encode(ch),
                            b'SIZE',
                            0,
                            4,
                            p_amount,
                            0,
                            b'FVCA',
                            0,
                            p_amount * 12
                        )

                    elif self._channelTypes[i] == 'DoubleVectorArray':
                        data = struct.pack(
                            '>4sLQ' + str(tempNameLength) + 's4sLQ2L4sLQ',
                            b'CHNM',
                            0,
                            len(ch) + 1,
                            str.encode(ch),
                            b'SIZE',
                            0,
                            4,
                            p_amount,
                            0,
                            b'DVCA',
                            0,
                            p_amount * 24
                        )

                    elif self._channelTypes[i] == 'DoubleArray':
                        data = struct.pack(
                            '>4sLQ' + str(tempNameLength) + 's4sLQ2L4sLQ',
                            b'CHNM',
                            0,
                            len(ch) + 1,
                            str.encode(ch),
                            b'SIZE',
                            0,
                            4,
                            p_amount,
                            0,
                            b'DVCA',
                            0,
                            p_amount * 8
                        )

                f.write(data)

                if self._channelTypes[i] == 'FloatVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f4').tostring())
                elif self._channelTypes[i] == 'DoubleVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f8').tostring())
                elif self._channelTypes[i] == 'DoubleArray':
                    f.write(pointsArray.reshape(-1).astype('>f8').tostring())

                if self._format == 'mcx':
                    if self._channelTypes[i] == 'FloatVectorArray':
                        if (p_amount * 3 * 4) % 8 != 0:
                            f.write(struct.pack('>L', 0))

            f.flush()

    def getChannels(self):
        return self._channels

    def setChannels(self, channels):
        self._channels = channels

    def getChannelTypes(self):
        return self._channelTypes

    def getPointArray(self):
        return self._pointsArray

    def setPointArray(self, pArray):
        self._pointsArray = pArray

    def getAmount(self):
        self._p_amount = 0
        for i in self._pointsArray[:]:
            self._p_amount += len(i)
        return self._p_amount

    def getPath(self):
        self.__genPath()
        return self._path

    def getTime(self):
        return int(self._frame * self._ticks_pre_frame)

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

    def getEleAmounts(self):
        return self._ele_amounts

    def __genNameLength(self, ch):
        _unit = 4 if self._format == 'mcc' else 8
        _ch_len = len(ch)

        tempNameLength = _ch_len + _unit
        if _ch_len % _unit:
            tempNameLength -= _ch_len % _unit

        return tempNameLength

    def __genHead(self):
        if self._format == 'mcc':
            self._head = struct.pack(
                self.__mcc_head_unpack_string,
                b'FOR4',
                40,
                b'CACHVRSN',
                4,
                808333568,
                b'STIM',
                4,
                self.getTime(),
                b'ETIM',
                4,
                self.getTime()
            )

        elif self._format == 'mcx':
            self._head = struct.pack(
                self.__mcx_head_unpack_string, b'FOR8',
                0,
                76,
                b'CACHVRSN',
                0,
                4,
                808333568,
                0,
                b'STIM',
                0,
                4,
                self.getTime(),
                0,
                b'ETIM',
                0,
                4,
                self.getTime(),
                0
            )

        else:
            return

    def __genPath(self):
        if self._format == 'mcc':
            self._path = self._xmlpath.replace(
                '.xml', 'Frame' + str(self._frame) + '.mc')
        elif self._format == 'mcx':
            self._path = self._xmlpath.replace(
                '.xml', 'Frame' + str(self._frame) + '.mcx')
        else:
            return


class NPCacheXML(NCacheXML):

    def __init__(self,
                 xml_path,
                 name='nParticleShape',
                 attrs=None,
                 chTypes=None):
        """"""
        super(NPCacheXML, self).__init__(xml_path)

        attrs = attrs or ['id', 'count', 'position']
        chTypes = chTypes or [0, 0, 1]

        self.__name = name
        self._channelInters = attrs
        self.setAttrs(attrs)
        self.setChannelTypes(chTypes)

    def getName(self):
        channels = self.getChannels()
        for ch in channels:
            if ch.endswith('_id'):
                self.__name = '_'.join(ch.split('_')[:-1])
                return self.__name

    def setName(self, name):
        self.__name = name
        self._channels = []
        for attr in self._channelInters:
            self._channels.append('_'.join([self.__name, attr]))

    def setAttrs(self, attrs):
        self._channels = []
        self._channelInters = attrs
        for attr in self._channelInters:
            self._channels.append('_'.join([self.__name, attr]))

    def getAttrs(self):
        return self._channelInters

    def setChannelTypes(self, chTypes):
        self._channelTypes = []
        for chType in chTypes:
            if chType == 0:
                self._channelTypes.append('DoubleArray')
            elif chType == 1:
                self._channelTypes.append('FloatVectorArray')
            elif chType == 2:
                self._channelTypes.append('DoubleVectorArray')
            else:
                raise

    def appendAttr(self, attr, attrType):
        if attrType == 0:
            attrType = 'DoubleArray'
        elif attrType == 1:
            attrType = 'FloatVectorArray'
        elif attrType == 2:
            attrType = 'DoubleVectorArray'
        else:
            raise ValueError
        chName = '_'.join([self.__name, attr])
        self.appendChannel(chName, chType=attrType, chInter=attr)


class NPCacheMC(NCacheMC):
    def __init__(self, xml_path, *args, **kwargs):
        super(NPCacheMC, self).__init__(xml_path, *args, **kwargs)
        self._xml = NPCacheXML(xml_path)
        self._xml.read()
        self._channels = self._xml.getChannels()
        self._channelTypes = self._xml.getChannelTypes()
        self.__name = self._xml.getName()

    def getName(self):
        return self.__name

    def getAttrs(self):
        return self._xml.getChannelInters()

    def getAttrValues(self, attr):
        chName = '_'.join([self.getName(), attr])
        index = self.getChannels().index(chName)
        return self.getPointArray()[index]

    def getStartFrame(self):
        return self._xml.getStartFrame()

    def getEndFrame(self):
        return self._xml.getEndFrame()


"""
if __name__ == '__main__':
    path = ['D:/temp/ncache/p32.xml', 'D:/temp/ncache/p32d.xml', 'D:/temp/ncache/p64.xml', 'D:/temp/ncache/p64d.xml']
    #path = ['D:/temp/ncache1/nParticleShape1.xml']
    for xml in path:
        print xml
        x = NPCacheXML(xml)

    #xml_path = 'D:/temp/ncache_p/np.xml'
    xml_path = 'D:/temp/ncache4/nParticleShape1.xml'
    #xml_path = path[2]
    xml = NPCacheXML(xml_path)
    xml.setStartFrame(1)
    xml.setEndFrame(48)
    xml.read()

    print xml.getChannelTypes()
    #print xml.getChannelTypes()

    #xml.write()


    mc = NPCacheMC(xml_path)
    for i in range(1,5):
 
        mc.setFrame(i)
        if mc.read():
            for attr in mc.getAttrs():
                if attr == 'count':
                    print attr
                    print mc.getAttrValues(attr)
        #print mc.getAttrValues('radiusPP')
        #mc.write()
"""
