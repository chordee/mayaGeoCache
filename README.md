# mayaGeoCache

這是之前為了交換檔案寫給 Maya Geo Cache 的 python class，用來讀寫 Maya Geo Cache，後來增加支援至 nParticle Cache。但只支援 One File Per Frame 的格式 
不管是 Geo Cache 還是 nParticle Cache 都重度仰賴一開始產生的 XML 檔，所以如果需要寫入請勿先用 XML class 產生正確的 XML file。  


#class NCacheXML 
NCacheXML(xml, fps = 24, startFrame = 1, endFrame = 200, channel = ['Shape',], cacheFormat = 'mcc', cacheType = 'OneFilePerFrame')  
*xml 為 xml file 的路徑位置*  

read() *讀取已存在的 xml 內容*  
write() *將目前的內容寫入 xml*  
 
setXMLPath(xml) *指定新的 xml 路徑*   
setFps(fps)  
setStartFrame(frame)     
setEndFrame(frame)  
setChannels(ch)  
setFormat(fmt) fmt = 'mcc' or 'mcx'     
appendChannel(chName, chType = 'FloatVectorArray', chInter = "positions")  
setChannelInters(chInters)  
  
getChannels() *回傳目前所有 channel 的字串 list*
 
getFps()   
getStartFrame()  
getEndFrame()  
getXMLString() *回傳目前的 XML 的文字內容*  
getFormat() * return 'mcc' or 'mcx' *  
getChannelInters()  
 
NCacheMC(xml_path, frame = 1, channel = ['Shape',], pointsArray = [[[0,0,0],],])
