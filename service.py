import xbmc
import xbmcgui
import xbmcaddon
import json
import threading
from datetime import datetime, timedelta, time
import urllib
import urllib2
import random
import time
import os

if xbmc.getCondVisibility("System.HasAddon(plugin.video.xbmb3c)"):
    __settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    __cwd__ = __settings__.getAddonInfo('path')
    BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources/lib' ) )
    sys.path.append(BASE_RESOURCE_PATH)

class SkinHelper ():

    addonSettings = None
    favorites_art_links = []
    favoriteshows_art_links = []
    channels_art_links = []
    global_art_links = []
    musicvideo_art_links = []
    photo_art_links = []
    current_fav_art = 0
    current_favshow_art = 0
    current_channel_art = 0
    current_musicvideo_art = 0
    current_photo_art = 0
    current_global_art = 0
    fullcheckinterval = 3600
    shortcheckinterval = 60
    _userId = ""

    doDebugLog = False

    def logMsg(self, msg, level = 1):
        if self.doDebugLog == True:
            xbmc.log(msg)

    def findNextLink(self, linkList, startIndex, filterOnName):
        currentIndex = startIndex

        isParentMatch = False

        while(isParentMatch == False):

            currentIndex = currentIndex + 1

            if(currentIndex == len(linkList)):
                currentIndex = 0

            if(currentIndex == startIndex):
                return (currentIndex, linkList[currentIndex])

            isParentMatch = True
            if(filterOnName != None and filterOnName != ""):
                isParentMatch = filterOnName in linkList[currentIndex]["collections"]

        nextIndex = currentIndex + 1

        if(nextIndex == len(linkList)):
            nextIndex = 0

        return (nextIndex, linkList[currentIndex])                 


    def updateCollectionArtLinks(self):

        from DownloadUtils import DownloadUtils
        downloadUtils = DownloadUtils()        

        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')

        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')
        userid = self._userId

        if userName == "":
            self.logMsg("[MB3 SkinHelper] updateCollectionArtLinks -- xbmb3c username empty, skipping task")
            return False
        else:
            self.logMsg("[MB3 SkinHelper] updateCollectionArtLinks -- xbmb3c username: " + userName)

        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/Root?format=json"
        jsonData = downloadUtils.downloadUrl(userUrl, suppress=True, popup=0 )

        result = json.loads(jsonData)

        parentid = result.get("Id")

        userRootPath = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?ParentId=&SortBy=SortName&Fields=CollectionType,Overview,RecursiveItemCount&format=json"
        jsonData = downloadUtils.downloadUrl(userRootPath, suppress=True, popup=0 )

        result = json.loads(jsonData)
        result = result.get("Items")

        artLinks = {}
        collection_count = 0
        WINDOW = xbmcgui.Window( 10000 )

        # process collections
        for item in result:

            collectionType = item.get("CollectionType", "")
            name = item.get("Name")
            childCount = item.get("RecursiveItemCount")
            if(childCount == None or childCount == 0):
                continue

            # Process collection item Backdrops
            self.logMsg("[MB3 SkinHelper get Collection Images Movies and Series]")
            collectionUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?&SortOrder=Descending&ParentId=" + item.get("Id") + "&IncludeItemTypes=Movie,Series,MusicVideo&Fields=ParentId,Overview&SortOrder=Descending&Recursive=true&CollapseBoxSetItems=false&format=json"
            jsonData = downloadUtils.downloadUrl(collectionUrl, suppress=True, popup=0 )  
            collectionResult = json.loads(jsonData)

            self.logMsg("[MB3 SkinHelper COLLECTION] -- " + item.get("Name") + " -- " + collectionUrl)

            collectionResult = collectionResult.get("Items")
            if(collectionResult == None):
                collectionResult = []   

            for col_item in collectionResult:

                id = col_item.get("Id")
                name = col_item.get("Name")
                MB3type = col_item.get("Type")
                images = col_item.get("BackdropImageTags")
                images2 = col_item.get("ImageTags")

                stored_item = artLinks.get(id)

                if(stored_item == None):

                    stored_item = {}
                    collections = []
                    collections.append(item.get("Name"))
                    stored_item["collections"] = collections
                    links = []
                    images = col_item.get("BackdropImageTags")
                    images2 = col_item.get("ImageTags")
                    parentID = col_item.get("ParentId")
                    name = col_item.get("Name")
                    if (images == None):
                        images = []
                    if (images2 == None):
                        images2 = []                    

                    index = 0
                    count = 0

                    if images != []:
                        for backdrop in images:
                            # only get first image
                            while not count == 1:
                                try:
                                    info = {}
                                    info["url"] = downloadUtils.getArtwork(col_item, "Backdrop")
                                    info["type"] = MB3type
                                    info["index"] = index
                                    info["id"] = id
                                    info["parent"] = parentID
                                    info["name"] = name
                                    links.append(info)
                                    if self.doDebugLog:
                                        self.logMsg("[MB3 SkinHelper Backdrop:] -- " + name + " -- " + info["url"])
                                    index = index + 1
    
                                    stored_item["links"] = links
                                    artLinks[id] = stored_item
                                    
                                except Exception, e:
                                    self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))
                                count += 1


                else:
                    stored_item["collections"].append(item.get("Name"))


            # Process collection item Photos
            self.logMsg("[MB3 SkinHelper get Collection Images Photos]")
            collectionUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?Limit=20&SortOrder=Descending&ParentId=" + item.get("Id") + "&IncludeItemTypes=Photo&Fields=ParentId,Overview&SortOrder=Descending&Recursive=true&CollapseBoxSetItems=false&format=json"
            jsonData = downloadUtils.downloadUrl(collectionUrl, suppress=True, popup=0 )  
            collectionResult = json.loads(jsonData)

            self.logMsg("[MB3 SkinHelper COLLECTION] -- " + item.get("Name") + " -- " + collectionUrl)

            collectionResult = collectionResult.get("Items")
            if(collectionResult == None):
                collectionResult = []   

            for col_item in collectionResult:

                id = col_item.get("Id")
                name = col_item.get("Name")
                MB3type = col_item.get("Type")
                images = col_item.get("ImageTags")

                stored_item = artLinks.get(id)

                if(stored_item == None):

                    stored_item = {}
                    collections = []
                    collections.append(item.get("Name"))
                    stored_item["collections"] = collections
                    links = []
                    images = col_item.get("ImageTags")
                    parentID = col_item.get("ParentId")
                    name = col_item.get("Name")
                    if (images == None):
                        images = []

                    index = 0

                    if(col_item.get("Type") == "Photo"):
                        for imagetag in images:
                            try:
                                info = {}
                                info["url"] = downloadUtils.getArtwork(col_item, "Primary")
                                info["type"] = MB3type
                                info["index"] = index
                                info["id"] = id
                                info["parent"] = parentID
                                info["name"] = name
                                links.append(info)
                                index = index + 1
                                if self.doDebugLog:
                                    self.logMsg("[MB3 SkinHelper Photo Thumb:] -- " + name + " -- " + info["url"])
                                stored_item["links"] = links
                                artLinks[id] = stored_item
                            except Exception, e:
                                self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))


                        stored_item["links"] = links
                        artLinks[id] = stored_item
                else:
                    stored_item["collections"].append(item.get("Name"))
                    
            
            # Process collection item Music and all Other
            self.logMsg("[MB3 SkinHelper get Collection Images Other]")
            collectionUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?&SortOrder=Descending&ParentId=" + item.get("Id") + "&IncludeItemTypes=MusicArtist,MusicAlbum,Audio&Fields=ParentId,Overview&SortOrder=Descending&Recursive=true&CollapseBoxSetItems=false&format=json"
            jsonData = downloadUtils.downloadUrl(collectionUrl, suppress=True, popup=0 )  
            collectionResult = json.loads(jsonData)

            self.logMsg("[MB3 SkinHelper COLLECTION] -- " + item.get("Name") + " -- " + collectionUrl)

            collectionResult = collectionResult.get("Items")
            if(collectionResult == None):
                collectionResult = []   

            for col_item in collectionResult:

                id = col_item.get("Id")
                name = col_item.get("Name")
                MB3type = col_item.get("Type")
                images = col_item.get("ImageTags")
                
                stored_item = artLinks.get(id)
                
                if(stored_item == None):
                    stored_item = {}
                    collections = []
                    collections.append(item.get("Name"))
                    stored_item["collections"] = collections
                    links = []
                    images2 = col_item.get("ImageTags")
                    images = col_item.get("BackdropImageTags")
                    parentID = col_item.get("ParentId")
                    name = col_item.get("Name")
                    if (images == None):
                        images = []
                    if (images == None):
                        images2 = []                    

                    index = 0
                    
                    for imagetag in images:
                        try:
                            info = {}
                            info["url"] = downloadUtils.getArtwork(col_item, "Backdrop", index=str(index))
                            info["type"] = MB3type
                            info["index"] = index
                            info["id"] = id
                            info["parent"] = parentID
                            info["name"] = name
                            links.append(info)
                            index = index + 1
                            if self.doDebugLog:
                                self.logMsg("[MB3 SkinHelper Backdrop:] -- " + name + " -- " + info["url"])
                            stored_item["links"] = links
                            artLinks[id] = stored_item
                        except Exception, e:
                            self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))                    
                    
                    if images == []:
                        for imagetag in images2:
                            try:
                                info = {}
                                info["url"] = downloadUtils.getArtwork(col_item, "Primary", index=str(index))
                                info["type"] = MB3type
                                info["index"] = index
                                info["id"] = id
                                info["parent"] = parentID
                                info["name"] = name
                                links.append(info)
                                index = index + 1
                                if self.doDebugLog:
                                    self.logMsg("[MB3 SkinHelper Primary:] -- " + name + " -- " + info["url"])
                                stored_item["links"] = links
                                artLinks[id] = stored_item
                            except Exception, e:
                                self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))
                                              

                        stored_item["links"] = links
                        artLinks[id] = stored_item
                else:
                    stored_item["collections"].append(item.get("Name"))            

        collection_count = collection_count + 1

        # build global link list
        final_global_art = []

        for id in artLinks:
            item = artLinks.get(id)
            collections = item.get("collections")
            links = item.get("links")

            for link_item in links:
                link_item["collections"] = collections
                final_global_art.append(link_item)

        self.global_art_links = final_global_art
        random.shuffle(self.global_art_links)

        return True        



    def setBackgroundLink(self, windowPropertyName, filterOnCollectionName):

        WINDOW = xbmcgui.Window( 10000 )
        backGroundUrl = ""

        if (filterOnCollectionName == "favoritemovies"):
            if(len(self.favorites_art_links) > 0):
                next, nextItem = self.findNextLink(self.favorites_art_links, self.current_fav_art, "")
                self.current_fav_art = next
                backGroundUrl = nextItem["url"]
        elif (filterOnCollectionName == "favoriteshows"):
            if(len(self.favoriteshows_art_links) > 0):
                next, nextItem = self.findNextLink(self.favoriteshows_art_links, self.current_favshow_art, "")
                self.current_favshow_art = next
                backGroundUrl = nextItem["url"]
        elif (filterOnCollectionName == "channels"):
            if(len(self.channels_art_links) > 0):
                next, nextItem = self.findNextLink(self.channels_art_links, self.current_channel_art, "")
                self.current_channel_art = next
                backGroundUrl = nextItem["url"]
        elif (filterOnCollectionName == "musicvideos"):
            if(len(self.musicvideo_art_links) > 0):
                next, nextItem = self.findNextLink(self.musicvideo_art_links, self.current_musicvideo_art, "")
                self.current_musicvideo_art = next
                backGroundUrl = nextItem["url"]
        elif (filterOnCollectionName == "photos"):
            if(len(self.photo_art_links) > 0):
                next, nextItem = self.findNextLink(self.photo_art_links, self.current_photo_art, "")
                self.current_photo_art = next
                backGroundUrl = nextItem["url"]
        else:
            if(len(self.global_art_links) > 0):
                next, nextItem = self.findNextLink(self.global_art_links, self.current_global_art, filterOnCollectionName)
                self.current_global_art = next
                backGroundUrl = nextItem["url"]
                
        if "/10000/10000/" in backGroundUrl:        
            backGroundUrl = backGroundUrl.split("/10000/10000/",1)[0]
            backGroundUrl_small = backGroundUrl
            backGroundUrl = backGroundUrl + "/1920/1080/0?"
            backGroundUrl_small = backGroundUrl_small + "/620/350/0?"
        else:
            backGroundUrl_small = backGroundUrl
        
        WINDOW.setProperty(windowPropertyName, backGroundUrl)
        WINDOW.setProperty(windowPropertyName + ".small", backGroundUrl_small)

    def updateTypeArtLinks(self):

        from DownloadUtils import DownloadUtils
        downloadUtils = DownloadUtils()        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')

        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')
        userid = self._userId

        if userName == "":
            self.logMsg("[MB3 SkinHelper] -- xbmb3c username empty, skipping task")
            return False
        else:
            self.logMsg("[MB3 SkinHelper] updateTypeArtLinks-- xbmb3c username: " + userName)

        # load Favorite Movie BG's
        favMoviesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=20&Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Movie&Filters=IsFavorite&format=json"
        jsonData = downloadUtils.downloadUrl(favMoviesUrl, suppress=True, popup=0 )
        result = json.loads(jsonData)

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            count = 0
            for backdrop in images:
                while not count == 1:
                    try:                
                        info = {}
                        info["url"] = downloadUtils.getArtwork(item, "Backdrop", index=str(index))
                        info["index"] = index
                        info["id"] = id
                        info["parent"] = parentID
                        info["name"] = name
                        self.logMsg("BG Favorite Movie Image Info : " + str(info), level=0)
        
                        if (info not in self.favorites_art_links):
                            self.favorites_art_links.append(info)
                        index = index + 1
                    except Exception, e:
                        self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))
                    count += 1                    

        random.shuffle(self.favorites_art_links)       

        # load Favorite TV Show BG's
        favShowsUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=20&Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Series&Filters=IsFavorite&format=json"
        jsonData = downloadUtils.downloadUrl(favShowsUrl, suppress=True, popup=0 )
        result = json.loads(jsonData)

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            count = 0
            for backdrop in images:
                while not count == 1:
                    try:                
                        info = {}
                        info["url"] = downloadUtils.getArtwork(item, "Backdrop", index=str(index))
                        info["index"] = index
                        info["id"] = id
                        info["parent"] = parentID
                        info["name"] = name
                        self.logMsg("BG Favorite Shows Image Info : " + str(info), level=0)
        
                        if (info not in self.favoriteshows_art_links):
                            self.favoriteshows_art_links.append(info)
                        index = index + 1
                    except Exception, e:
                        self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))
                    count += 1                    

        random.shuffle(self.favoriteshows_art_links)    

        # load Music Video BG's
        musicMoviesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=40&SortOrder=Descending&Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=MusicVideo&format=json"
        jsonData = downloadUtils.downloadUrl(musicMoviesUrl, suppress=True, popup=0 )
        result = json.loads(jsonData)

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            count = 0
            for backdrop in images:
                while not count == 1:
                    try:                
                        info = {}
                        info["url"] = downloadUtils.getArtwork(item, "Backdrop", index=str(index))
                        info["index"] = index
                        info["id"] = id
                        info["parent"] = parentID
                        info["name"] = name
                        self.logMsg("BG MusicVideo Image Info : " + str(info), level=0)
        
                        if (info not in self.musicvideo_art_links):
                            self.musicvideo_art_links.append(info)
                        index = index + 1
                    except Exception, e:
                            self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))
                    count += 1                    

        random.shuffle(self.musicvideo_art_links)

        # load Photo BG's
        photosUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=20&SortOrder=Descending&Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Photo&format=json"
        jsonData = downloadUtils.downloadUrl(photosUrl, suppress=True, popup=0 )
        result = json.loads(jsonData)

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            index = 0
            
            try: 
                info = {}
                info["url"] = downloadUtils.getArtwork(item, "Primary", index=str(index))
                info["index"] = index
                info["id"] = id
                info["parent"] = parentID
                info["name"] = name
    
                if (info not in self.photo_art_links):
                    self.photo_art_links.append(info)
                index = index + 1
            except Exception, e:
                    self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))         

        random.shuffle(self.photo_art_links)       

        # load Channels BG links
        channelsUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Channels?&SortOrder=Descending&format=json"
        jsonData = downloadUtils.downloadUrl(channelsUrl, suppress=True, popup=0 )
        result = json.loads(jsonData)        

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            plot = item.get("Overview")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
                try:
                    info = {}
                    info["url"] = downloadUtils.getArtwork(item, "Backdrop", index=str(index))
                    info["index"] = index
                    info["id"] = id
                    info["plot"] = plot
                    info["parent"] = parentID
                    info["name"] = name
                    self.logMsg("BG Channel Image Info : " + str(info), level=0)
                except Exception, e:
                        self.logMsg("[MB3 SkinHelper] error occurred: " + str(e))             

            if (info not in self.channels_art_links):
                self.channels_art_links.append(info)    
            index = index + 1

        random.shuffle(self.channels_art_links)

        return True         

    def waitForAbort(self, timeout):
        while (True):
            if timeout == 0:
                return False

            if (xbmc.abortRequested):
                xbmc.log("[MB3 SkinHelper] XBMC Shutdown detected....exiting now")
                return True

            time.sleep(timeout)
            timeout -= 1
            
    def getContentFromCache(self):
        WINDOW = xbmcgui.Window( 10000 )
        self.logMsg("[MB3 SkinHelper] get properties from cache...")
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.xbmb3c)"):
            linkCount = 0
            while linkCount !=10:
                mbstring = "titanmb3." + str(linkCount)
                if xbmc.getInfoLabel("Skin.String(" + mbstring + '.title)') != "":
                    WINDOW.setProperty(mbstring + '.title', xbmc.getInfoLabel("Skin.String(" + mbstring + '.title)'))
                    WINDOW.setProperty(mbstring + '.image', xbmc.getInfoLabel("Skin.String(" + mbstring + '.image)'))
                    WINDOW.setProperty(mbstring + '.path', xbmc.getInfoLabel("Skin.String(" + mbstring + '.path)'))
                linkCount += 1

        if xbmc.getCondVisibility("System.HasAddon(plugin.video.plexbmc)"):
            linkCount = 0
            while linkCount !=10:
                plexstring = "plexbmc." + str(linkCount)
                if xbmc.getInfoLabel("Skin.String(" + plexstring + '.title)') != "":
                    WINDOW.setProperty(plexstring + '.title', xbmc.getInfoLabel("Skin.String(" + plexstring + '.title)'))
                    WINDOW.setProperty(plexstring + '.image', xbmc.getInfoLabel("Skin.String(" + plexstring + '.image)'))
                    WINDOW.setProperty(plexstring + '.path', xbmc.getInfoLabel("Skin.String(" + plexstring + '.path)'))
                linkCount += 1        

    def setContentInCache(self):         
        WINDOW = xbmcgui.Window( 10000 )
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.xbmb3c)"):
            linkCount = 0
            while linkCount !=10:
                mbstring = "titanmb3." + str(linkCount)
                if WINDOW.getProperty(mbstring + '.title') != "":
                    xbmc.executebuiltin('Skin.SetString(' + mbstring + '.title,' + WINDOW.getProperty(mbstring + '.title') + ")")
                    xbmc.executebuiltin('Skin.SetString(' + mbstring + '.image,' + WINDOW.getProperty(mbstring + '.image') + ")")
                    xbmc.executebuiltin('Skin.SetString(' + mbstring + '.path,' + WINDOW.getProperty(mbstring + '.path') + ")")
                else:
                    xbmc.executebuiltin('Skin.Reset(' + mbstring + '.title)')
                    xbmc.executebuiltin('Skin.Reset(' + mbstring + '.image)')
                    xbmc.executebuiltin('Skin.Reset(' + mbstring + '.path)')
                linkCount += 1 

    def run(self):
        self.logMsg("Started")

        fullcheckinterval_current = 0
        shortcheckinterval_current = 0

        doAbort = False
        while (not doAbort):

            # get the user ID
            WINDOW = xbmcgui.Window( 10000 )
            self._userId = WINDOW.getProperty("userid")

            self.logMsg("[MB3 SkinHelper] userId: " + self._userId)
            self.logMsg("[MB3 SkinHelper] fullscan interval currently " + str(fullcheckinterval_current))
            self.logMsg("[MB3 SkinHelper] shortscan interval currently " + str(shortcheckinterval_current))

            # only perform actions if xbmb3c addon is present
            if xbmc.getCondVisibility("System.HasAddon(plugin.video.xbmb3c)"):

                # get images from server only if fullcheckinterval has reached
                if fullcheckinterval_current <= 0:
                    self.logMsg("[MB3 SkinHelper] loading images from server...")
                    
                    # do not perform actions if player is running as it may cause stutter
                    if xbmc.getCondVisibility("Player.HasVideo"):
                        self.logMsg("[MB3 SkinHelper] ...skipped - video playing...")
                    else:
                        # load images
                        if self._userId == "":
                            self.getContentFromCache()
                        else:
                            self.updateMB3links()
                            self.setContentInCache()
    
                            updateResult = False
                            try:
                                updateResult = self.updateTypeArtLinks()
                                self.updateMB3links()
                                updateResult = self.updateCollectionArtLinks()
                            except Exception, e:
                                self.logMsg(str(e))                            
    
                            if (updateResult == True):
                                fullcheckinterval_current = self.fullcheckinterval                    
                                self.logMsg("[MB3 SkinHelper] ...load images complete")                 
                            else:
                                self.logMsg("[MB3 SkinHelper] ...load images failed, will try again later")

                # set pictures on properties only every X seconds    
                if shortcheckinterval_current <= 0:
                    self.logMsg("[MB3 SkinHelper] setting tile images")
                    
                    if xbmc.getCondVisibility("Player.HasVideo"):
                        self.logMsg("[MB3 SkinHelper] ...skipped - video playing...")
                    else:                    
                        # try to get from cache first
                        if self._userId == "":
                            self.getContentFromCache()
                        else:
                            # some global backgrounds
                            self.setBackgroundLink("xbmb3c.std.movies.3.image", "favoritemovies")
                            self.setBackgroundLink("xbmb3c.std.tvshows.4.image", "favoriteshows")
                            self.setBackgroundLink("xbmb3c.std.channels.0.image", "channels")
                            self.setBackgroundLink("xbmb3c.std.music.3.image", "musicvideos")
                            self.setBackgroundLink("xbmb3c.std.photo.0.image", "photos")
    
                            # set MB3 content links
                            self.updateMB3links()                    
                            linkCount = 0
    
                            while linkCount !=10:
                                mbstring = "titanmb3." + str(linkCount)
                                self.logMsg("set backgroundlink for: " + mbstring)
                                if not "virtual" in WINDOW.getProperty(mbstring + ".type"):
                                    self.setBackgroundLink(mbstring + ".image", WINDOW.getProperty(mbstring + ".title"))
                                linkCount += 1
    
                            self.setContentInCache()
    
                    self.logMsg("[MB3 SkinHelper] setting images complete")
                    shortcheckinterval_current = self.shortcheckinterval

            fullcheckinterval_current -= 2
            shortcheckinterval_current -= 2
            doAbort = self.waitForAbort(2)


    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def updateMB3links(self):
        win = xbmcgui.Window( 10000 )
        
        # global items update
        backGroundString = "MB3.Background.Music.FanArt"
        backGroundUrl = win.getProperty(backGroundString)
        if "/10000/10000/" in backGroundUrl:
            backGroundUrl = backGroundUrl.split("/10000/10000/",1)[0]
            backGroundUrl = backGroundUrl + "/620/350/0"
        win.setProperty(backGroundString + ".small", backGroundUrl)
        
        backGroundString = "MB3.Background.Movie.FanArt"
        backGroundUrl = win.getProperty(backGroundString)
        if "/10000/10000/" in backGroundUrl:
            backGroundUrl = backGroundUrl.split("/10000/10000/",1)[0]
            backGroundUrl = backGroundUrl + "/620/350/0"
        win.setProperty(backGroundString + ".small", backGroundUrl)
        
        backGroundString = "MB3.Background.TV.FanArt"
        backGroundUrl = win.getProperty(backGroundString)
        if "/10000/10000/" in backGroundUrl:
            backGroundUrl = backGroundUrl.split("/10000/10000/",1)[0]
            backGroundUrl = backGroundUrl + "/620/350/0"
        win.setProperty(backGroundString + ".small", backGroundUrl)
        
        #set boxsets collapsed for movies
        link = win.getProperty("xbmb3c.std.movies.0.path")
        link = link.replace("&mode=0,return)", "")
        link = link + "%26CollapseBoxSetItems%3Dtrue&mode=0,return)"
        win.setProperty("xbmb3c.std.movies.0.collapsed.path", link)        
        print("[MB3 SkinHelper] boxsets --> " + link)
        
        # collection items update
        linkCount = 0
        while linkCount !=10:
            orgmbstring = "xbmb3c." + str(linkCount)
            mbstring = "titanmb3." + str(linkCount)

            if "mediabrowser" in win.getProperty(orgmbstring + ".recent.path"):
                win.setProperty(mbstring + ".title", win.getProperty(orgmbstring + ".title"))
                win.setProperty(mbstring + ".type", win.getProperty(orgmbstring + ".type"))
                win.setProperty(mbstring + ".fanart", win.getProperty(orgmbstring + ".fanart"))
                win.setProperty(mbstring + ".recent.path", win.getProperty(orgmbstring + ".recent.path"))
                win.setProperty(mbstring + ".unwatched.path", win.getProperty(orgmbstring + ".unwatched.path"))
                if win.getProperty(orgmbstring + ".type") == "tvshows":
                    win.setProperty(mbstring + ".inprogress.path", win.getProperty(orgmbstring + ".nextepisodes.path"))
                else:
                    win.setProperty(mbstring + ".inprogress.path", win.getProperty(orgmbstring + ".inprogress.path"))

                win.setProperty(mbstring + ".genre.path", win.getProperty(orgmbstring + ".genre.path"))
                
                if win.getProperty(orgmbstring + ".collapsed.path") != "":
                    win.setProperty(mbstring + ".path", win.getProperty(orgmbstring + ".collapsed.path"))
                else:
                    win.setProperty(mbstring + ".path", win.getProperty(orgmbstring + ".path"))

                link = win.getProperty(orgmbstring + ".recent.path")
                link = link.replace("ActivateWindow(VideoLibrary,", "")
                link = link.replace(",return)", "")
                win.setProperty(mbstring + ".recent.content", link)

                if "musicvideo" in win.getProperty(orgmbstring + ".type"):
                    win.setProperty("xbmb3c.std.music.3.content", link)                

                link = win.getProperty(orgmbstring + ".unwatched.path")
                link = link.replace("ActivateWindow(VideoLibrary,", "")
                link = link.replace(",return)", "")
                win.setProperty(orgmbstring + ".unwatched.content", link)

                if win.getProperty(orgmbstring + ".inprogress.path") != "":
                    link = win.getProperty(orgmbstring + ".inprogress.path")
                    link = link.replace("ActivateWindow(VideoLibrary,", "")
                    link = link.replace(",return)", "")
                    win.setProperty(mbstring + ".inprogress.content", link)  
                
                if win.getProperty(orgmbstring + ".nextepisodes.path") != "":
                    link = win.getProperty(orgmbstring + ".nextepisodes.path")
                    link = link.replace("ActivateWindow(VideoLibrary,", "")
                    link = link.replace(",return)", "")
                    win.setProperty(mbstring + ".nextepisodes.content", link)
                    win.setProperty(mbstring + ".inprogress.content", link)

            linkCount += 1

xbmc.log("[MB3 SkinHelper] Started... fetching background images now")
pollingthread = SkinHelper()
pollingthread.run()