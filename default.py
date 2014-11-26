import xbmcplugin
import xbmcgui
import shutil
import xbmcaddon
import os
import time
import urllib

# function to set the current view permanent in the xbmb3c addon
def setView(containerType,viewId):

    if viewId=="00":
        win = xbmcgui.Window( 10000 )
        curView = xbmc.getInfoLabel("Container.Viewmode")
        
        # get all views from views-file
        skin_view_file = os.path.join(xbmc.translatePath('special://skin'), "views.xml")
        skin_view_file_alt = os.path.join(xbmc.translatePath('special://skin/extras'), "views.xml")
        if xbmcvfs.exists(skin_view_file_alt):
            skin_view_file = skin_view_file_alt
        try:
            tree = etree.parse(skin_view_file)
        except:           
            sys.exit()
        
        root = tree.getroot()
        
        for view in root.findall('view'):
            if curView == view.attrib['id']:
                viewId=view.attrib['value']
    else:
        viewId=viewId    

    if xbmc.getCondVisibility("System.HasAddon(plugin.video.xbmb3c)"):
        __settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __settings__.setSetting(xbmc.getSkinDir()+ '_VIEW_' + containerType, viewId)

elif action == "SETRECOMMENDEDMB3SETTINGS":   
    setRecommendedMBSettings(argument1)      
        
def setRecommendedMBSettings(skin):
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    
    if skin == "titan":
        addonSettings.setSetting('includePeople', 'false')
        addonSettings.setSetting('showIndicators', 'false')
        addonSettings.setSetting('showArtIndicators', 'false')
        addonSettings.setSetting('useMenuLoader', 'false')       
        
        
#script init
action = ""
argument1 = ""
argument2 = ""
argument3 = ""

# get arguments
try:
    action = str(sys.argv[1])
except: 
    pass

try:
    argument1 = str(sys.argv[2])
except: 
    pass

try:
    argument2 = str(sys.argv[3])
except: 
    pass

try:
    argument3 = str(sys.argv[4])
except: 
    pass  

# select action
if action == "SETVIEW":
    setView(argument1, argument2)
elif action == "SETRECOMMENDEDMB3SETTINGS":   
    setRecommendedMBSettings(argument1)   