# mayaGeoCache I/O

這是之前為了交換檔案寫給 Maya Geo Cache 的 python class，用來讀寫 Maya Geo Cache，後來增加支援至 nParticle Cache。但只支援 One File Per Frame 的格式 
不管是 Geo Cache 還是 nParticle Cache 都重度仰賴一開始產生的 XML 檔，所以如果需要寫入請務必先用 XML class 產生正確的 XML file。


# class NCacheXML
NCacheXML(xml, fps = 24, startFrame = 1, endFrame = 200, channel = ['Shape',], cacheFormat = 'mcc', cacheType = 'OneFilePerFrame')  
*xml 為 xml file 的路徑位置*  

read() *讀取已存在的 xml 內容*  

write() *將目前的內容寫入 xml*  

  
setXMLPath(xml) *指定新的 xml 路徑*

setFps(fps)

setStartFrame(frame)

setEndFrame(frame)

setChannels(ch)

setFormat(fmt) * fmt = 'mcc' or 'mcx' *

appendChannel(chName, chType = 'FloatVectorArray', chInter = "positions")

setChannelTypes(ch_types) * str List 包含 'FloatVectorArray' or 'DoubleVectorArray' 如果是 Geo Cache 建議所有 Channel 都一樣*

setChannelInters(chInters)

  
getChannels() *回傳目前所有 channel 的字串 list*

 
getFps()

getStartFrame()

getEndFrame()

getXMLString() *回傳目前的 XML 的文字內容*

getFormat() * return 'mcc' or 'mcx' *

getChannelTypes()

getChannelInters()

# class Cache File

NCacheMC(xml_path, frame = 1, channel = ['Shape',], pointsArray = [[[0,0,0],],])  

*cache 檔的路徑由 xml_path 和 frame 自動產生，pointArray 為 numpy array 的 list*

read() *讀取 cache 檔內容*

write() *寫入 cache 檔內容*

setFrame(frame)

setXMLPath(xml_path)

setChannels(channels)

setPointArray(pArray) *pArray 為 List 裡面放置 numpy 2D array*

getAmount() *回傳總共 points 數量*

getFrame()

getPath() *回傳目前 cache 檔的路徑位置*

getCannelTypes()

getEleAmounts() *List: 回傳各個 cahnnel 的點數量*

getPointArray()

# class NPCacheXML

繼承自 NCacheXML，是 nParticle Cache 專用的 XML class，有針對 Particle 的屬性操作新增 function。nParticle 的 Channel 和 PointArray 都會因為屬性的內容具有不同的類型和長度，用 attr 取代本來的 Channel Interpretation。Channel 名稱也用 nParticle name 和 attrs 自動產生。因為每個屬性會具有不同類型，Channel Type 為了方便改為整數標記。預設具有 count、id、position 屬性。id 屬性為必須傭有。

0 = 'DoubleArray

1 = 'FloatVectorArray'

2 = 'DoubleVectorArray'

NPCacheXML(xml_path, name = 'nParticleShape', attrs = ['id', 'count', 'position'], chTypes = [0, 0, 1])

setName(name)

setAttrs(attrs) *str list*

setChannelTypes(chTypes) *int list*

appendAttr(attr, attrType) *attr: str，attrType: int*

getName()

# class NPCacheMC

繼承自 NCacheMC 具有 attr 操作的 function。attr value 因屬性不同會具有不同長度的 numpy array。

NPCacheMC(xml)

getName()

getAttrs()

getAttrValues(attr) *取得屬性的 numpy array*

getStartFrame()

getEndFrame()
