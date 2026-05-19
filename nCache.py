import math
import os.path
import struct
import xml.etree.ElementTree as ET

import numpy as np


# Maya stores cache time in "ticks"; one tick = 1/6000 second. Frame ticks
# are computed as frame_number * (TICKS_PRE_SECOND / fps).
TICKS_PRE_SECOND = 6000

# Cache version string "0.1\0" packed as a big-endian uint32 (0x302E3100).
# Written into the header's CACHVRSN chunk.
_CACHE_VERSION = 0x302E3100


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
                 evalStep=1.0,  # evaluate every x frame
                 channels=None,
                 cacheFormat='mcc',
                 cacheType='OneFilePerFrame'):
        channels = channels or ['Shape', ]

        self._fps = int(fps)
        self._xml = None
        self._startFrame = int(startFrame)
        self._endFrame = int(endFrame)
        self._channels = channels
        self._format = cacheFormat
        self._type = cacheType
        self._samplingRate = None
        self._channelTypes = []
        self._channelInters = []

        self.setXMLPath(xml)
        self.setSamplingRate(evalStep)

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
        self._channelTypes = []
        self._channelInters = []

        for em in root.findall('Channels'):
            for child in em:
                self._channels.append(child.attrib['ChannelName'])
                self._channelTypes.append(child.attrib['ChannelType'])
                self._channelInters.append(child.attrib['ChannelInterpretation'])
                # Use last channel's samplingRate
                self._samplingRate = int(child.attrib['SamplingRate'])

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

    def setSamplingRate(self, step):
        self._samplingRate = int(float(step) * self.getTimePerFrame())

    def getSamplingRate(self):
        return self._samplingRate

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

        timePerFrame = self.getTimePerFrame()
        cacheType = self._type

        self._xml_str = '''<Autodesk_Cache_File>
  <cacheType Type="{cacheType}" Format="{format}"/>
  <time Range="{startFrame}-{endFrame}"/>
  <cacheTimePerFrame TimePerFrame="{perFrame}"/>
  <cacheVersion Version="2.0"/>
  <Channels>\n'''.format(
            cacheType=cacheType,
            format=self._format,
            startFrame=int(self._startFrame * timePerFrame),
            endFrame=int(self._endFrame * timePerFrame),
            perFrame=int(timePerFrame),
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
                'SamplingRate="%d"' % int(self._samplingRate),
                'StartTime="%d"' % int(self._startFrame * timePerFrame),
                'EndTime="%d"' % int(self._endFrame * timePerFrame),
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

    def getTimePerFrame(self):
        return int(TICKS_PRE_SECOND / self._fps)

    def getType(self):
        return self._type

    def setXMLPath(self, xml):
        if not xml.lower().endswith(".xml"):
            xml += ".xml"
        self._xml = xml

    def getXMLPath(self):
        return self._xml

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
    """One-file-per-frame Maya cache data file (.mc / .mcx).

    Writes always emit the OFPF binary layout (header + a single block, no
    per-block TIME chunk); the current frame's tick value is encoded in the
    header's STIM/ETIM fields.
    """
    def __init__(self,
                 xml_path,
                 frame=1,
                 channels=None,
                 pointsArray=None):
        channels = channels or ['Shape', ]
        pointsArray = pointsArray or [[[0, 0, 0], ], ]

        xml = NCacheXML(xml_path)
        xml_path = xml.getXMLPath()
        if os.path.exists(xml_path):
            xml.read()

        # mcc header: 48 bytes, FOR4 container with 32-bit chunk lengths.
        #   'FOR4' u32_len 'CACHVRSN' 4 version 'STIM' 4 start 'ETIM' 4 end
        self.__mcc_head_unpack_string = '>4sL8sLl4sLl4sLl'
        # mcx header: 92 bytes, FOR8 container with 64-bit chunk lengths.
        self.__mcx_head_unpack_string = '>4sLQ8sLQ2L4sLQ2l4slQ2l'
        self._xmlpath = xml_path

        self._type = xml.getType()
        self._format = xml.getFormat()
        self._channelTypes = xml.getChannelTypes()
        self._xml = xml

        self._time = 0
        self._time_pre_frame = xml.getTimePerFrame()
        self._sampling_rate = xml.getSamplingRate()
        self.setFrame(frame)

        self.__genPath()
        self.__genHead()
        self._channels = channels
        self._pointsArray = pointsArray
        self._p_amount = 0
        self._ele_amounts = []

        for i in pointsArray:
            self._p_amount += np.array(i).size / 3

    def read(self):
        if not self._xmlpath or not os.path.isfile(self._xmlpath):
            raise Exception("XML file not exists: %s" % self._xmlpath)

        xml = NCacheXML(self._xmlpath)
        xml.read()

        self._xml = xml
        self._format = xml.getFormat()
        self._channels = xml.getChannels()
        self._channelTypes = xml.getChannelTypes()
        self._sampling_rate = xml.getSamplingRate()

        self.__genPath()
        if self._path is None:
            raise Exception("No valid cache file found in: %s"
                            % os.path.dirname(self._xmlpath))
        if not os.path.isfile(self._path):
            raise Exception("Cache file not exists: %s" % self._path)

        file = open(self._path, 'rb')

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
                file.read(name_length)
                temp = struct.unpack('>4s2L4sl', file.read(20))
                step += 8 + name_length + 20 + temp[4]

                if temp[3] == b'FVCA':
                    self._ele_amounts.append(temp[4] / 12)
                    pos = struct.unpack(
                        '>' + str(temp[2] * 3) + 'f',
                        file.read(temp[4])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float32).reshape(-1, 3))

                elif temp[3] == b'DVCA':
                    self._ele_amounts.append(temp[4] / 24)
                    pos = struct.unpack(
                        '>' + str(temp[2] * 3) + 'd',
                        file.read(temp[4])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float64).reshape(-1, 3))

                elif temp[3] == b'DBLA':
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
                file.read(name_length)
                temp = struct.unpack('>4sLQ2L4sLQ', file.read(40))
                step_push = int(math.ceil(float(temp[7]) / 8) * 8)
                step += 16 + name_length + 40 + step_push

                if temp[5] == b'FVCA':
                    self._ele_amounts.append(temp[7] / 12)
                    pos = struct.unpack(
                        '>' + str(temp[3] * 3) + 'f',
                        file.read(temp[7])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float32).reshape(-1, 3))

                elif temp[5] == b'DVCA':
                    self._ele_amounts.append(temp[7] / 24)
                    pos = struct.unpack(
                        '>' + str(temp[3] * 3) + 'd',
                        file.read(temp[7])
                    )
                    self._pointsArray.append(
                        np.array(pos, dtype=np.float64).reshape(-1, 3))

                elif temp[5] == b'DBLA':
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
                        amount_size += len(i) * 2

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
                            b'DBLA',
                            0,
                            p_amount * 8
                        )

                f.write(data)

                if self._channelTypes[i] == 'FloatVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f4').tobytes())
                elif self._channelTypes[i] == 'DoubleVectorArray':
                    f.write(pointsArray.reshape(-1).astype('>f8').tobytes())
                elif self._channelTypes[i] == 'DoubleArray':
                    f.write(pointsArray.reshape(-1).astype('>f8').tobytes())

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
        return int(self._time)

    def setFrame(self, frame):
        self._time = int(frame * self._time_pre_frame)

    def getFrame(self):
        return self._time / self._time_pre_frame

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
        # On-disk channel name = name bytes + NULL terminator, padded with
        # extra NULL bytes so the total length is a multiple of 4 (mcc) or
        # 8 (mcx). When len(ch) is already aligned, a full unit of padding
        # is still appended.
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
                _CACHE_VERSION,
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
                _CACHE_VERSION,
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
        ext = {"mcc": ".mc", "mcx": ".mcx"}.get(self._format, "")

        time_str = 'Frame%d' % int(self.getFrame())
        tick = self._time % self._time_pre_frame
        if tick:
            time_str += 'Tick%d' % tick

        self._path = self._xmlpath.replace('.xml', time_str + ext)


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


def houdini_geo_export():
    """Export a Houdini point geometry sequence as a Maya geometry cache.

    Each unique value of the prim 'name' string attribute becomes one channel
    in the Maya geo cache. The name must match the Maya shape node name for
    Maya to load it. Topology must be static across frames.

    Source geometry must be baked (e.g. File Cache SOP / bgeo sequence).
    A live DOP simulation connected directly will not produce correct results
    because geometryAtFrame() does not drive DOP cooking.
    """
    import hou  # noqa
    import threading

    node = hou.pwd()
    sop = hou.node(hou.pwd().path() + '/WRITE_OUT')
    fps = hou.fps()

    start_frame = node.parm('start_frame').eval()
    end_frame = node.parm('end_frame').eval()
    eval_rate = node.parm('eval_rate').eval()
    xml_path = node.parm('xml').eval()
    name_attr_name = node.parm('name_attr').eval()

    ref_geo = sop.geometryAtFrame(start_frame)
    name_attr = ref_geo.findPrimAttrib(name_attr_name)
    if name_attr is None:
        raise RuntimeError("Prim '%s' attribute not found." % name_attr_name)
    if name_attr.dataType() != hou.attribData.String:
        raise RuntimeError("Prim '%s' attribute must be a string type." % name_attr_name)
    channels = [n for n in dict.fromkeys(ref_geo.primStringAttribValues(name_attr_name)) if n]

    xml = NCacheXML(xml_path, fps=fps, startFrame=start_frame,
                    endFrame=end_frame, evalStep=eval_rate, channels=channels)
    xml.write()

    sampling_rate = xml.getSamplingRate()
    time_per_frame = xml.getTimePerFrame()

    with hou.InterruptableOperation(
            "Cache", "Caching", open_interrupt_dialog=True) as operation:

        threads = []
        for frame_whole in range(start_frame, end_frame + 1):
            for tick in range(0, time_per_frame, sampling_rate):
                frame = frame_whole + (tick / time_per_frame)
                if frame > end_frame:
                    break

                geo = sop.geometryAtFrame(frame)
                all_pos = np.frombuffer(
                    geo.pointFloatAttribValuesAsString('P'),
                    dtype=np.float32
                ).reshape(-1, 3)

                point_array = []
                for ch in channels:
                    indices = sorted(set(
                        pt.number()
                        for prim in geo.prims()
                        if prim.attribValue(name_attr_name) == ch
                        for pt in prim.points()
                    ))
                    point_array.append(all_pos[indices])

                mc = NCacheMC(xml_path, frame=frame, channels=channels,
                              pointsArray=point_array)
                th = threading.Thread(target=mc.write)
                th.start()
                threads.append(th)

                _pro = float(frame - start_frame) / (end_frame - start_frame)
                _msg = "Exporting Frame %d from %d to %d" % (frame, start_frame, end_frame)
                operation.updateLongProgress(_pro, _msg)

        for th in threads:
            th.join()


def houdini_export():
    """Export a Houdini point geometry sequence as an nParticle cache.

    Reads parameters from the wrapping HDA (start_frame, end_frame, eval_rate,
    particle_name, xml). The Houdini attribute-to-Maya-attribute mapping below
    MUST stay in sync with `_hou_geo_data`, which appends arrays to the cache
    in the same order.
    """
    import hou  # noqa
    import threading

    node = hou.pwd()
    sop = hou.node(hou.pwd().path() + '/WRITE_OUT')
    fps = hou.fps()

    start_frame = node.parm('start_frame').eval()
    end_frame = node.parm('end_frame').eval()
    eval_rate = node.parm('eval_rate').eval()
    pname = node.parm('particle_name').eval()

    attrs = [x.name() for x in sop.geometryAtFrame(start_frame).pointAttribs()]
    xml_path = node.parm('xml').eval()

    xml = NPCacheXML(xml_path)
    xml.setName(pname + 'Shape')
    xml.setFps(fps)
    xml.setStartFrame(start_frame)
    xml.setEndFrame(end_frame)
    xml.setSamplingRate(eval_rate)

    if 'v' in attrs:
        xml.appendAttr('velocity', 1)
    if 'age' in attrs:
        xml.appendAttr('age', 0)
    if 'life' in attrs:
        xml.appendAttr('lifespanPP', 0)
    if 'pscale' in attrs:
        xml.appendAttr('radiusPP', 0)
    if 'Cd' in attrs:
        xml.appendAttr('rgbPP', 1)
    if 'Alpha' in attrs:
        xml.appendAttr('opacityPP', 0)
    if 'rotation' in attrs:
        xml.appendAttr('rotationPP', 1)

    xml.write()
    sampling_rate = xml.getSamplingRate()
    time_per_frame = xml.getTimePerFrame()

    visual_warning_once = True
    with hou.InterruptableOperation(
            "Cache", "Caching", open_interrupt_dialog=True) as operation:

        threads = []
        for frame_whole in range(start_frame, end_frame + 1):
            for tick in range(0, time_per_frame, sampling_rate):
                frame = frame_whole + (tick / time_per_frame)
                if frame > end_frame:
                    break

                geo = sop.geometryAtFrame(frame)

                check_id_attr = geo.findPointAttrib('id')
                if check_id_attr is None and visual_warning_once:
                    hou.ui.displayMessage(
                        'Point id attribute not found at frame %f' % frame
                    )
                    visual_warning_once = False
                    break

                data_array = _hou_geo_data(geo, attrs)

                mc = NPCacheMC(xml_path)
                mc.setPointArray(data_array)
                mc.setFrame(frame)

                th = threading.Thread(target=mc.write)
                th.start()
                threads.append(th)

                _pro = float(frame - start_frame) / (end_frame - start_frame)
                _msg = "Exporting Frame %d from %d to %d" % (frame, start_frame, end_frame)
                operation.updateLongProgress(_pro, _msg)

        for th in threads:
            th.join()


def _hou_geo_data(geo, attrs):
    """Collect Houdini point attributes as a list of numpy arrays.

    The append order here MUST match the channel order produced by
    `houdini_export` via `NPCacheXML.appendAttr`; channel index alignment
    between XML and binary is what lets Maya map data back to attributes.
    """
    import hou  # noqa

    data_array = []

    def _int_64(attr):
        return geo.pointIntAttribValuesAsString(
            attr, int_type=hou.numericData.Int64
        )

    def _float_32(attr):
        return geo.pointFloatAttribValuesAsString(
            attr
        )

    def _float_64(attr):
        return geo.pointFloatAttribValuesAsString(
            attr, float_type=hou.numericData.Float64
        )

    id_array = np.frombuffer(_int_64('id'), dtype=np.int64)
    data_array.append(id_array)

    count_array = np.array([len(geo.points())])
    data_array.append(count_array)

    pos_array = np.frombuffer(_float_32('P'), dtype=np.float32).reshape(-1, 3)
    data_array.append(pos_array)

    if 'v' in attrs:
        vel_array = np.frombuffer(_float_32('v'), dtype=np.float32).reshape(-1, 3)
        data_array.append(vel_array)

    if 'age' in attrs:
        age_array = np.frombuffer(_float_64('age'), dtype=np.float64)
        data_array.append(age_array)

    if 'life' in attrs:
        life_array = np.frombuffer(_float_64('life'), dtype=np.float64)
        data_array.append(life_array)

    if 'pscale' in attrs:
        pscale_array = np.frombuffer(_float_64('pscale'), dtype=np.float64)
        data_array.append(pscale_array)

    if 'Cd' in attrs:
        cd_array = np.frombuffer(_float_32('Cd'), dtype=np.float32).reshape(-1, 3)
        data_array.append(cd_array)

    if 'Alpha' in attrs:
        alpha_array = np.frombuffer(_float_64('Alpha'), dtype=np.float64)
        data_array.append(alpha_array)

    if 'rotation' in attrs:
        rotation_array = np.frombuffer(_float_32('rotation'), dtype=np.float32).reshape(-1, 3)
        data_array.append(rotation_array)

    return data_array
