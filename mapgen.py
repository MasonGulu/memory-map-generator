import PySimpleGUI as sg

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

memoryBlockTemplate = {
    'startSegment': 0,
    'startOffset': 0,
    'endSegment': 0x0100,
    'endOffset': 0,
    'label': '',
    'color': 0x550000 # Red for now, might make it randomly generated at some point
}


def memoryBlockGUI(memoryBlock=memoryBlockTemplate):
    backup = memoryBlock
    # Size constants
    segBoxWidth = 9
    fullBoxWidth = 11
    dashPaddingWidth = 18
    # End size constants
    startFrameLayout = [
        [sg.Text('Segment:',size=(segBoxWidth,1)), sg.Input(hexString(memoryBlock['startSegment']), 
            size=(segBoxWidth,1), key='startSegment', enable_events=True)],
        [sg.Text('Offset:',size=(segBoxWidth,1)), sg.Input(hexString(memoryBlock['startOffset']), 
            size=(segBoxWidth,1), key='startOffset', enable_events=True)],
        [sg.Text('-'*dashPaddingWidth + ' OR ' + '-'*dashPaddingWidth)],
        [sg.Text('Full address:'), sg.Input(hexString(calculateFullAddr(memoryBlock['startSegment'], memoryBlock['startOffset']),5), 
            size=(fullBoxWidth,1), key='startFullAddr', enable_events=True)]
            # I tried to stay within PEP 8, but this line is just oh god oh fuck
    ]
    endFrameLayout = [
        [sg.Text('Segment:',size=(segBoxWidth,1)), sg.Input(hexString(memoryBlock['endSegment']), 
            size=(segBoxWidth,1), key='endSegment', enable_events=True)],
        [sg.Text('Offset:',size=(segBoxWidth,1)), sg.Input(hexString(memoryBlock['endOffset']), 
            size=(segBoxWidth,1), key='endOffset', enable_events=True)],
        [sg.Text('-'*dashPaddingWidth + ' OR ' + '-'*dashPaddingWidth)],
        [sg.Text('Full address:'), sg.Input(hexString(calculateFullAddr(memoryBlock['endSegment'], memoryBlock['endOffset']),5), 
            size=(fullBoxWidth,1), key='endFullAddr', enable_events=True)],
        [sg.Text('-'*dashPaddingWidth + ' OR ' + '-'*dashPaddingWidth)],
        [sg.Text('Length:',size=(segBoxWidth,1)), sg.Input(hexString(calculateSize(memoryBlock['startSegment'], 
            memoryBlock['startOffset'], memoryBlock['endSegment'], memoryBlock['endOffset'])),size=(segBoxWidth,1),key='length', enable_events=True)]
            # You'd think I was kidding
    ]
    infoFrameLayout = [
        [sg.Text('Label:'), sg.Input(memoryBlock['label'],size=(fullBoxWidth,1),key='label', enable_events=True)],
        [sg.Text('Color:'), sg.Input(hexString(memoryBlock['color'], 6),size=(fullBoxWidth,1),key='color', enable_events=True),
            sg.ColorChooserButton(' ',button_color=(None, memoryBlock['color']),key='chooser')]
    ]

    layout = [
        [sg.Text('Create or Edit a Memory Block')],
        [sg.Frame('Info', infoFrameLayout)],
        [sg.Frame('Start', startFrameLayout)],
        [sg.Frame('End', endFrameLayout)],
        [sg.Cancel(key='cancel'),sg.Submit(key='submit')]
    ]
    win = sg.Window('Memory Block GUI', layout)
    while True:
        event, values = win.read()

        if (event == sg.WIN_CLOSED) or (event == 'cancel'):
            return backup
        
        if (event == 'submit'):
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
                if values['color'][0] == '#':
                    values['color'] = '0x' + values['color'][1:]
                win['color'].update(value=values['color'])
                win['chooser'].update(button_color=(None, int(values['color'],0)))
                memoryBlock['color'] = values[int(values['color'], 0)]

            if (event == 'label'):
                memoryBlock['label'] = values['label']

            if not lenmod:
                win['length'].update(value=hexString(calculateSize(memoryBlock['startSegment'],memoryBlock['startOffset'],memoryBlock['endSegment'],memoryBlock['endOffset'])))


            win.finalize() 
        except:
            print("Exception occured!")
    
memoryBlockGUI()
### End function declaration

# First we must gather some information including:
# Maximum pixel height and width of graph
# Starting address, ending address, length
# Color of base graph
# Calculate how many bytes each pixel represents

