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

setChannelInters(chInters)

  
getChannels() *回傳目前所有 channel 的字串 list*

 
getFps()

getStartFrame()

getEndFrame()

getXMLString() *回傳目前的 XML 的文字內容*

getFormat() * return 'mcc' or 'mcx' *

getChannelInters()

# Cache File Class #

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
