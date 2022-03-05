from tkinter import Checkbutton
from PIL import ImageGrab
import PySimpleGUI as sg
import copy
import math
import pickle
import logging

# TODO
# Change to dark theme
# Add text color customization for memory "blocks"
# Change memory "blocks" to classes
# If I can, make it not ugly
# Eventually implement if __name__ == "__main__"

sg.theme("DarkBlack")
logging.basicConfig(level=logging.DEBUG)
### Function declaration


def hexString(number, minLen=4):
    # Takes in 2 ints: number and minLen. number is the number to be converted to hex
    # And minLen is the minimum length of the hex string it returns, expressed in characters
    # 2 characters per byte. After writing this function I discovered hex() exists...
    # Keeping this function because I like how it looks (plus minLen is useful)
    retString = ''
    hexTable = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
    while (number > 0 or len(retString) < minLen):
        tmpNum = number & 0xF
        # Isolate the lower 4 bits
        retString = hexTable[tmpNum] + retString
        number = number >> 4
    return ('0x' + retString)

def calculateFullAddr(segment, offset):
    return (segment << 4) + offset

def calculateSize(segment1, offset1, segment2, offset2):
    return calculateFullAddr(segment2, offset2) - calculateFullAddr(segment1, offset1) 

def calculateFullStartAddr(block):
    return calculateFullAddr(block['startSegment'], block['startOffset'])

def calculateFullEndAddr(block):
    return calculateFullAddr(block['endSegment'], block['endOffset'])

def bytesToPixel(bytes):
    return math.floor(bytes/mapInfo['bytePixel'])

def drawRelativeRect(x, y, width, height, color='grey'):
    win['graph'].draw_rectangle((x,y), ((x+width), (y+height)), fill_color=color)


def topLeft(block, x=0, y=0):
    return (mapInfo['left']+bytesToPixel(calculateFullStartAddr(block)-mapInfo['startAddress'])+x,
        mapInfo['top']+y)

def topRight(block, x=0, y=0):
    return (mapInfo['left']+bytesToPixel(calculateFullEndAddr(block)-mapInfo['startAddress'])+x,
        mapInfo['top']+y)

def bottomLeft(block,x=0,y=0):
    return (mapInfo['left']+bytesToPixel(calculateFullStartAddr(block)-mapInfo['startAddress'])+x,
        mapInfo['top']+mapInfo['height']+y)

def bottomRight(block):
    return (mapInfo['left']+bytesToPixel(calculateFullEndAddr(block)-mapInfo['startAddress']),
        mapInfo['top']+mapInfo['height'])

def center(block):
    x = (topLeft(block)[0] + bottomRight(block)[0]) / 2
    y = (topLeft(block)[1] + bottomRight(block)[1]) / 2
    return (x, y)

memoryBlockTemplate = {
    'startSegment': 0,
    'startOffset': 0,
    'endSegment': 0x0100,
    'endOffset': 0,
    'label': '',
    'color': 'red',
    'textColor': 'black'
}

def memoryBlockGUI(memoryBlock=copy.deepcopy(memoryBlockTemplate)):
    backup = copy.deepcopy(memoryBlock)
    # Size constants
    segBoxWidth = 9
    fullBoxWidth = 11
    dashPaddingWidth = 18
    # End size constants
    startTabsLayout = [
        sg.Tab('Components', 
            [[sg.Text('Segment:',size=(segBoxWidth,1)), 
                sg.Input(hexString(memoryBlock['startSegment']), expand_x=True, key='startSegment', enable_events=True)],
            [sg.Text('Offset:',size=(segBoxWidth,1)), 
                sg.Input(hexString(memoryBlock['startOffset']), expand_x=True, key='startOffset', enable_events=True)]]),
        sg.Tab('Full Address',[
            [sg.Text('Full address:'), 
            sg.Input(hexString(calculateFullAddr(memoryBlock['startSegment'], 
                memoryBlock['startOffset']),5), expand_x=True, key='startFullAddr', enable_events=True)]])
    ]
    endTabsLayout = [
        sg.Tab('Components',
            [[sg.Text('Segment:',size=(segBoxWidth,1)), sg.Input(hexString(memoryBlock['endSegment']), 
                expand_x=True, key='endSegment', enable_events=True)],
            [sg.Text('Offset:',size=(segBoxWidth,1)), sg.Input(hexString(memoryBlock['endOffset']), 
                expand_x=True, key='endOffset', enable_events=True)]]),
        sg.Tab('Full Address',
            [[sg.Text('Full address:'), sg.Input(hexString(calculateFullAddr(memoryBlock['endSegment'], memoryBlock['endOffset']),5), 
                expand_x=True, key='endFullAddr', enable_events=True)]]),
        sg.Tab('Length',
            [[sg.Text('Length:'), sg.Input(hexString(calculateSize(memoryBlock['startSegment'],
                memoryBlock['startOffset'], memoryBlock['endSegment'], memoryBlock['endOffset'])),expand_x=True,size=(segBoxWidth,1),key='length', enable_events=True)]])
    ]
    infoFrameLayout = [
        [sg.Text('Label: '), sg.Input(memoryBlock['label'],size=(fullBoxWidth,1),key='label', enable_events=True, expand_x=True)],
        [sg.Text('Color: '), sg.Input(memoryBlock['color'],size=(fullBoxWidth,1),key='color', enable_events=True, expand_x=True),
            sg.ColorChooserButton(' ',button_color=(None, memoryBlock['color']),key='chooser')],
        [sg.Text('TColor:'), sg.Input(memoryBlock['textColor'],size=(fullBoxWidth,1),key='textColor', enable_events=True, expand_x=True),
            sg.ColorChooserButton(' ',button_color=(None, memoryBlock['color']), key="textColorChooser")]
    ]

    layout = [
        [sg.Text('Create or Edit a Memory Block')],
        [sg.Frame('Info', infoFrameLayout, expand_x=True)],
        [sg.Frame('Start', [[sg.TabGroup([startTabsLayout])]]),
            sg.Frame('End', [[sg.TabGroup([endTabsLayout])]])],
        [sg.Cancel(key='cancel'),sg.Submit(key='submit')]
    ]
    win = sg.Window('Memory Block GUI', layout)
    while True:
        event, values = win.read()

        if (event == sg.WIN_CLOSED) or (event == 'cancel'):
            win.close()
            return False
        
        if (event == 'submit'):
            win.close()
            return memoryBlock
        
        try:
            lenmod = False
            if (event == 'startSegment') or (event == 'startOffset'):
                # The segment:offset was updated, update the full address
                memoryBlock['startSegment'] = int(values['startSegment'],0)
                memoryBlock['startOffset'] = int(values['startOffset'],0)
                win['startFullAddr'].update(value = hexString(calculateFullAddr(memoryBlock['startSegment'], memoryBlock['startOffset']),5))
            
            if (event == 'startFullAddr'):
                # Updated the full address, so now update the segment:offset
                memoryBlock['startSegment'] = (int(values['startFullAddr'],0) & 0xffff0) >> 4
                memoryBlock['startOffset'] = (int(values['startFullAddr'],0) & 0x0000f)
                win['startSegment'].update(value=hexString(memoryBlock['startSegment']))
                win['startOffset'].update(value=hexString(memoryBlock['startOffset']))
            
            if (event == 'length'):
                values['endOffset']=hexString(memoryBlock['startOffset']+int(values['length'],0))
                values['endSegment']=hexString(memoryBlock['startSegment'])
                win['endSegment'].update(value=(values['endSegment']))
                win['endOffset'].update(value=(values['endOffset']))
                event = 'endOffset'
                lenmod = True

            if (event == 'endSegment') or (event == 'endOffset'):
                # The segment:offset was updated, update the full address
                memoryBlock['endSegment'] = int(values['endSegment'],0)
                memoryBlock['endOffset'] = int(values['endOffset'],0)
                win['endFullAddr'].update(value = hexString(calculateFullAddr(memoryBlock['endSegment'], memoryBlock['endOffset']),5))
            
            if (event == 'endFullAddr'):
                # Updated the full address, so now update the segment:offset
                memoryBlock['endSegment'] = (int(values['endFullAddr'],0) & 0xffff0) >> 4
                memoryBlock['endOffset'] = (int(values['endFullAddr'],0) & 0x0000f)
                win['endSegment'].update(value=hexString(memoryBlock['endSegment']))
                win['endOffset'].update(value=hexString(memoryBlock['endOffset']))
            
            if (event == 'color'):
                win['chooser'].update(button_color=(None, values['color']))
                memoryBlock['color'] = values['color']

            if (event == 'textColor'):
                win['textColorChooser'].update(button_color=(None, values['textColor']))
                memoryBlock['textColor'] = values['textColor']

            if (event == 'label'):
                memoryBlock['label'] = values['label']

            if not lenmod:
                win['length'].update(value=hexString(calculateSize(memoryBlock['startSegment'],memoryBlock['startOffset'],memoryBlock['endSegment'],memoryBlock['endOffset'])))


            win.finalize() 
        except ValueError:
            logging.info("Value in a input is not a number.")

def isAnythingClose(xpos, posTable):
    threshold = 8
    for x in posTable:
        if xpos <= x + threshold and xpos >= x - threshold:
            return True
    return False

# Taken from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Graph_Drawing_And_Dragging_Figures.py
def save_element_as_file(element, filename):
    """
    Saves any element as an image file.  Element needs to have an underlyiong Widget available (almost if not all of them do)
    :param element: The element to save
    :param filename: The filename to save to. The extension of the filename determines the format (jpg, png, gif, ?)
    """
    widget = element.Widget
    box = (widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_rootx() + widget.winfo_width(), widget.winfo_rooty() + widget.winfo_height())
    grab = ImageGrab.grab(bbox=box)
    grab.save(filename)

mapInfo = {
    'memoryBlocks': [],
    'startAddress': 0,
    'endAddress': 0xFFFFF,
    'color': 'white',
    'textColor': 'white',
    'width': 500,
    'height': 120
}

### End function declaration

# First we must gather some information including:
# Maximum pixel height and width of graph
# Starting address, ending address, length
# Color of base graph
# Calculate how many bytes each pixel represents

#layout = [
    #[sg.Text('Starting Address:'), sg.Input('0x00000',key='startAddress')],
    #[sg.Text('Ending Address:'), sg.Input('0xFFFFF',key='endAddress')],
    #[sg.Text('Color:'), sg.Input('0xFFFFFF',key='color'), sg.ColorChooserButton(' ',button_color=(None, mapInfo['color']),key='chooser')],
        # Like I said, fuck this
    #[sg.Text('Width:'), sg.Input('60', key='width')],
    #[sg.Text('Height:'), sg.Input('500', key='height')],
    #[sg.Submit()]
#]

layout = [
    [sg.Text('Starting Address:'), sg.Input('0x00000',key='startAddress',expand_x=True)],
    [sg.Text('Ending Address:'), sg.Input('0xFFFFF',key='endAddress',expand_x=True)],
    [sg.Text('Color:'), sg.Input('#FFFFFF',key='color',expand_x=True), sg.ColorChooserButton(' ',button_color=(None, mapInfo['color']),key='chooser')],
    [sg.Text('Text Color:'), sg.Input('#FFFFFF',key='textColor',expand_x=True), sg.ColorChooserButton(' ',button_color=(None, mapInfo['textColor']))],
    [sg.Text('Width:'), sg.Input('500', key='width',expand_x=True)],
    [sg.Text('Height:'), sg.Input('100', key='height',expand_x=True)],
    [sg.Submit()]
]

win = sg.Window('Memory Map Setup', layout)
event, values = win.read()
if event != "Submit":
    exit()
mapInfo['startAddress'] = int(values['startAddress'],0)
mapInfo['endAddress'] = int(values['endAddress'], 0)

#if values['color'][0] == '#':
    #values['color'] = '0x' + values['color'][1:]

mapInfo['color'] = values['color']
mapInfo['width'] = int(values['width'], 0)
mapInfo['height'] = int(values['height'], 0)

# Do some calculations
mapInfo['fWidth'] = math.floor(mapInfo['width']*1.2)
mapInfo['fHeight'] = math.floor(mapInfo['height']*2.4)
mapInfo['left'] = (mapInfo['fWidth'] - mapInfo['width']) / 2
mapInfo['top'] = (mapInfo['fHeight'] - mapInfo['height']) / 2
mapInfo['bytePixel'] = (mapInfo['endAddress'] - mapInfo['startAddress']) / mapInfo['width']

win.close()

layout = [
    [sg.Graph((mapInfo['fWidth'], mapInfo['fHeight']), (0,mapInfo['fHeight']), (mapInfo['fWidth'],0),key='graph')],
    [sg.Text('Zoom',size=(8,1)), 
        sg.Slider(range=(1,100), key='divisor',orientation='horizontal',enable_events=True, expand_x=True,disable_number_display=True)],
    [sg.Text('Location',size=(8,1)), 
        sg.Slider(range=(0,0), key='location',orientation='horizontal',enable_events=True,disable_number_display=True,expand_x=True)],
    [sg.Listbox(mapInfo['memoryBlocks'], size=(25,4), key='selectedBlock',expand_x=True), sg.VerticalSeparator(),
        sg.Button('New',key='new'), sg.Button('Edit',key='edit'), sg.Button('Delete',key='delete'),
        sg.Checkbox('Fit Camera to Segment', key='segCam', enable_events=True)],
    [sg.Checkbox('Enable Segment', key='segEnable', enable_events=True), sg.Input('0', size=(8,1),key='segment',enable_events=True),
        sg.Slider(range=(0,0xFFF0), orientation='h', key='segmentSlider', enable_events=True,
            expand_x=True, disable_number_display=True,resolution=0x0010)],
    [sg.Input(key='file'), sg.FileSaveAs('Browse'), sg.Button('Save', key='save'), sg.Button('Load',key='load'), sg.Button('SaveJPG',key='saveJPG')],
    
    
]

win = sg.Window('Memory Map', layout)

mapInfoBackup = copy.deepcopy(mapInfo)

while True:
    event, values = win.read()

    if (event == sg.WIN_CLOSED) or (event == 'cancel'):
        win.close()
        break
    
    values['angle'] = 60
    values['horOff'] = 4
    values['verOff'] = 5

    try:
        win['segment'].update(value=hexString(int(values['segment'],0),4))
    except:
        logging.info("Data in segment box is invalid.")

    mapInfo['startAddress'] = mapInfoBackup['startAddress']
    mapInfo['endAddress'] = mapInfoBackup['endAddress']
    mapInfo['bytePixel'] = mapInfoBackup['bytePixel']

    if (event == 'save'):
        try:
            with open(values['file'], 'wb') as file:
                pickle.dump(mapInfo, file)
                file.close()
        except:
            logging.warning("Invalid filename.")

    elif (event == 'load'):
        try:
            tmpwidth = mapInfo['width']
            tmpheight = mapInfo['height']
            with open(values['file'], 'rb') as file:
                mapInfo = pickle.load(file)
                mapInfoBackup = copy.deepcopy(mapInfo)
                file.close()
            mapInfo['width'] = tmpwidth
            mapInfo['height'] = tmpheight
            win['segmentSlider'].update(range=(mapInfo['startAddress']>>4, mapInfo['endAddress']>>4))
        except Exception as a:
            logging.warning("Invalid filename. %s",a)

    elif (event == 'segmentSlider'):
        try:
            win['segment'].update(value = hexString(int(values['segmentSlider']), 4))
            values['segment'] = hexString(int(values['segmentSlider']), 4)
        except:
            pass
        
    # Update zoom scale
    win['location'].update(range=(0,(values['divisor']-1)*10))
    values['location'] = values['location'] / 10
    lengthPerSegment = (mapInfo['endAddress'] - mapInfo['startAddress'])/values['divisor']
    mapInfo['startAddress'] = math.floor(lengthPerSegment*values['location'] + mapInfo['startAddress'])
    mapInfo['endAddress'] = math.ceil(lengthPerSegment + mapInfo['startAddress'])
    if (values['segCam'] and values['segEnable']):
        mapInfo['startAddress'] = int(values['segment'],0)<<4
        mapInfo['endAddress'] = mapInfo['startAddress'] + 0xFFFF
    mapInfo['bytePixel'] = (mapInfo['endAddress'] - mapInfo['startAddress']) / mapInfo['width']



    if (event == 'new'):
        a = memoryBlockGUI()
        if a:
            mapInfo['memoryBlocks'].append(copy.deepcopy(a))

    elif (event == 'delete'):
        del mapInfo['memoryBlocks'][labels.index(values['selectedBlock'][0])]
    
    elif (event == 'edit'):
        try:
            a = memoryBlockGUI(mapInfo['memoryBlocks'][labels.index(values['selectedBlock'][0])])
            if a:
                mapInfo['memoryBlocks'][labels.index(values['selectedBlock'][0])] = copy.deepcopy(a)
        except:
            print('Error in editing')

    elif (event == 'saveJPG'):
        try:
            save_element_as_file(win['graph'], values['file'])
        except ValueError:
            logging.info("Invalid filename.")

    # Reorganize memory blocks based off starting address
    notSorted = True
    while notSorted:
        notSorted = False
        for x in range(1, len(mapInfo['memoryBlocks'])):
            if calculateFullStartAddr(mapInfo['memoryBlocks'][x]) < calculateFullStartAddr(mapInfo['memoryBlocks'][x-1]):
                tmp = mapInfo['memoryBlocks'][x]
                mapInfo['memoryBlocks'][x] = mapInfo['memoryBlocks'][x-1]
                mapInfo['memoryBlocks'][x-1] = tmp
                notSorted = True
    
    # draw the graph
    win['graph'].erase()
    win['graph'].draw_rectangle((mapInfo['left'],mapInfo['top']),
        (mapInfo['left']+mapInfo['width'],mapInfo['top']+mapInfo['height']),
        fill_color=mapInfo['color'])
    win['graph'].draw_text(hexString(mapInfo['startAddress'],5), (mapInfo['left']-10,mapInfo['top']+(mapInfo['height']/2)),angle=90, color=mapInfo['textColor'])
    win['graph'].draw_text(hexString(mapInfo['endAddress'],5), (mapInfo['left']+mapInfo['width']+10,mapInfo['top']+(mapInfo['height']/2)),angle=90, color=mapInfo['textColor'])

    xposText = []
    labels = []
    for x in mapInfo['memoryBlocks']:
        labels.append(x['label'])
        win['graph'].draw_rectangle(topLeft(x), bottomRight(x), fill_color=x['color'])
        win['graph'].draw_text(x['label'], center(x), color = x['textColor'], angle=90)
        if not isAnythingClose(topLeft(x)[0]+values['horOff'], xposText):
            win['graph'].draw_text(hexString(calculateFullStartAddr(x),5), topLeft(x, values['horOff'], -values['verOff']), 
                text_location=sg.TEXT_LOCATION_LEFT, angle=values['angle'], color=mapInfo['textColor'])
            xposText.append(topLeft(x)[0]+values['horOff'])

        if not isAnythingClose(topRight(x)[0]-values['horOff'], xposText):
            win['graph'].draw_text(hexString(calculateFullEndAddr(x),5), topRight(x, -values['horOff'], -values['verOff']), 
                text_location=sg.TEXT_LOCATION_LEFT, angle=values['angle'], color=mapInfo['textColor'])
            xposText.append(topRight(x)[0]-values['horOff'])
        
        if values['segEnable']:
            # Show offset from current segment, if it's within a valid range
            try:
                if (calculateFullStartAddr(x) - (int(values['segment'],0)<<4) >= 0 and calculateFullStartAddr(x) - (int(values['segment'],0)<<4) <= 0xffff):
                    # Valid to show
                    win['graph'].draw_text(hexString(calculateFullStartAddr(x)-(int(values['segment'],0)<<4),4), bottomLeft(x, 0, values['verOff']),
                        text_location=sg.TEXT_LOCATION_RIGHT, angle=values['angle'], color=mapInfo['textColor'])
            except:
                pass
                # Fail silently as we're already printing a message about this
    if values['segEnable']:
        try:
            win['graph'].draw_line((mapInfo['left']+bytesToPixel((int(values['segment'],0)<<4)-mapInfo['startAddress']), mapInfo['top']),
            (mapInfo['left']+bytesToPixel((int(values['segment'],0)<<4)-mapInfo['startAddress']), mapInfo['top']+mapInfo['height']),
            color='grey', width=2)

            win['graph'].draw_line((mapInfo['left']+bytesToPixel((int(values['segment'],0)<<4)-mapInfo['startAddress']), mapInfo['top']+mapInfo['height']),
            (mapInfo['left']+bytesToPixel((int(values['segment'],0)<<4)-mapInfo['startAddress']+0xFFFF), mapInfo['top']+mapInfo['height']),
            color='grey', width=2)

            win['graph'].draw_line((mapInfo['left']+bytesToPixel((int(values['segment'],0)<<4)-mapInfo['startAddress']+0xFFFF), mapInfo['top']+mapInfo['height']),
            (mapInfo['left']+bytesToPixel((int(values['segment'],0)<<4)-mapInfo['startAddress']+0xFFFF), mapInfo['top']),
            color='grey', width=2)
        except:
            pass
    
    win['selectedBlock'].update(labels)
    win.finalize()