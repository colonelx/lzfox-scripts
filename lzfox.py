""" 
    LZFOX Control
    URL: https://github.com/colonelx/lzfox-scripts
"""

import serial, time, datetime, sys, re

class LZFOX:

    # Print is the only one that is being returned as "Mode:PRINT \r\n" <-- space, others are "Print:CLEAR\r\n", WHY!?
    MODES = [ 
        "CONTROL",              # Methods implemented
        "PRINT",                # Methods implemented
        "CLEAR",                # NOT implemented
        "READOUT",              # NOT implemented
        "CONTROL_WITH_READOUT", # NOT implemented
        "FROZEN_CONTROL",       # NOT implemented
        "FULL_READOUT",         # NOT implemented
        "WRITER"                # Partially implemented
    ]

    def __init__(self, port, baud):
        if not port or not baud:
            raise self.InputError("'port' and 'baud' are required!")
        self.port = port
        self.baud = baud
    
    # Decorator to check if we have an open Serial communication and opens one if none
    def _connection(func):
        def magic(self, *args, **kwargs):
            if not hasattr(self, 'ser'):
                self.connect()
            return func(self, *args, **kwargs)
        return magic

    # Helper method to parse the output. First line is either an Error or Empty
    def _readSerial(self):
        read_data = self.ser.readline()
        if read_data not in [b'\r\n', b'>\r\n']: # if first returned line is either of those, then there is no Error, else we throw an Exception
            raise self.IOError(read_data.decode('utf-8'))
        read_data = self.ser.readline()
        return read_data

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            self.ser.flush() # This is probably not needed!
        except:
            raise self.ConnectionError("Cannot connect to '{}', using baud rate={}".format(self.port, self.baud))
    
    @_connection
    def checkConnection(self):
        self.ser.write(b"\n")
        read_data = self.ser.readline()
        counter = 0

        # TODO: Those while cycles make no sense, if to be removed remember to fetch the second serial.readline()
        while counter < 6:
            read_data = self.ser.readline()
            if read_data[0:1] == '>':
                break
            else:
                counter +=1
            if counter == 3:
                self.ser.write(b"\n")
        counter = 0
        self.ser.write(b"\n")

        while counter < 6:
            read_data = self.ser.readline()
            if read_data[0:1] == '>':
                break
            else:
                counter +=1
            if counter == 3:
                self.ser.write(b"\n")

        time.sleep(0.1)
        self.ser.write(b"PING\n")
        time.sleep(0.1)
        read_data = self._readSerial()
        return read_data[0:4] == b'PONG'
          
    @_connection
    def getTime(self):
        self.ser.write(b"GET TIME\n")
        time.sleep(0.1) # this is bad!
        read_data = self._readSerial()
        match = re.search('.*:(\d+),.*', read_data.decode('utf-8'))
        timestmp = int(match[1]) if match else 0
        board_time = datetime.datetime.fromtimestamp(timestmp)
        return board_time 

    @_connection
    def getMode(self):
        self.ser.write(b"GET MODE\n")
        time.sleep(0.1) # this is bad!
        read_data = self._readSerial()
        match = re.search(".*:(.*) \\r\\n", read_data.decode('utf-8'))
        return match[1] if match else ''

    @_connection
    # TODO: You must be in Mode: Control, maybe implement a check?
    def getCtrl(self):
        self.ser.write(b"GET CTRL\n")
        time.sleep(0.5) # this is bad!
        read_data = self._readSerial().decode('utf-8')
        match = re.search('.*:([A-Z0-9]+)\s?.*', read_data)
        if not match:
            raise self.IOError("Invalid control returned '{}'".format(read_data))

        self.ser.readline() # obviously we have a '>' here as well !?
        return match[1]

    @_connection
    def getVersion(self):
        self.ser.write(b"GET VERSION\n")
        time.sleep(0.1) # this is bad!
        read_data = self._readSerial()
        match = re.search('.*:(.*)\\r\\n', read_data.decode('utf-8'))
        return match[1] if match else ''

    @_connection
    def getVoltage(self):
        self.ser.write(b"GET VOLTAGE\n")
        time.sleep(0.1) # this is bad!
        read_data = self._readSerial()
        match = re.search('.*:(.*)\\r\\n', read_data.decode('utf-8'))
        return match[1] if match else ''

    @_connection
    # TODO: This takes too much time, probably run in separate thread? But communication is single threaded, so lock Serial!
    def getBackup(self, filepath):
        self.ser.write(b"GET BACKUP\n")
        time.sleep(0.1) # this is bad!
        self.ser.readline() # the '>\r\n' line
        self.ser.readline() # the 'Backup:\r\n' line
        read = True
        i = 0
        n = 0
        MAX_LINES = 8192
       
        lines = []
        while read:
            i += 1
            read_data = self.ser.readline()
            if read_data == b'$\r\n': # I assume this is the final row
                read = False
            if read:
                lines.append(read_data.decode('utf-8'))
                percentage = i/MAX_LINES*100
                print("{:03.2f}% read".format(percentage))

        # TODO : see how will you store the backup.
        f = open(filepath, "w")
        f.writelines(lines)
        f.close()

        # TODO : this is just the export of valid rows ... see where will you need it
        for line in lines:
            match = re.search('\^ ([0-9A-F]+) ([0-9A-F]+) ([0-9A-F]+) ([0-9A-F]+),(\d+),.*#', line)
            if match:
                timestmp = datetime.datetime.fromtimestamp(int(match[5]))
                print(match[1], match[2], match[3], match[4], timestmp)

        read_line = self.ser.readline() # the '>' line
        return read_line == b'>'
        
    @_connection
    def setMode(self, mode):
        if mode not in self.MODES:
            raise self.InvalidModeError(mode)
        mode_enc = mode.encode('utf-8')
        self.ser.flush() # Probably not needed.
        self.ser.write(b"SET MODE " + mode_enc + b"\n")
        time.sleep(0.1) # Do we really need this ?
        read_data = self._readSerial()
        match = re.search('.*:([A-Z]+)\s?\\r\\n', read_data.decode('utf-8'))
        if not match or match[1] != mode:
            raise self.ModeSetError(mode, read_data)
        self.ser.readline() # fetch last '>'
        return True

    @_connection
    def setTime(self, new_time: datetime.datetime):
        self.ser.write(b"SET TIME " + new_time.strftime("%Y%m%d%H%M%S").encode('utf-8') + b'\n')
        time.sleep(0.1)
        read_data = self._readSerial()
        return read_data.decode('utf-8').startswith('Time:')
    
    @_connection
    # TODO: You must be in Mode: Control, maybe implement a check?
    def setControl(self, position):
        if not (position.isnumeric() and int(position) > 0 and int(position) <= 250) and (position not in ['START', 'FINISH']):
           raise self.InputError("Control position should be: [1..250] or [START,FINISH]")
        self.ser.write(b'SET CTRL ' + position.encode('utf-8') + b'\n') 
        time.sleep(0.1)

        read_data = self._readSerial()
        
        self.ser.readline() # the last '>' wtf!?
        return read_data.decode('utf-8').startswith('Control:'+position)

    @_connection
    # TODO: You must be in Mode: Writer, maybe implement a check? Also it is waiting for a card to become nearby, maybe set a timeout ... somehow?
    def writeInfo(self, info):
        self.ser.write(b"WRITE INFO " + info.encode('utf-8') + b"\n")
        time.sleep(0.1)
        waiting = True
        while waiting:
            ret = self.ser.readline()
            print('.',end=' ')
            if ret.decode('utf-8').startswith('WRITING INFO TO CARD: OK'):
                waiting = False
        print('\n')
        return True

    class Error(Exception):
        pass

    class InputError(Error):
        def __init__(self, message):
            self.message = message

        def __str__(self):
            return self.message

    class ConnectionError(Error):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

    class InvalidModeError(Error):
        def __init__(self, mode):
            self.message = "Invalid mode '{}' selected. Should be one of {}".format(mode, ','.join(LZFOX.MODES))
            super().__init__(self.message)

    class ModeSetError(Error):
        def __init__(self, mode, return_string):
            self.message = "Error setting mode '{}'. Returned string: '{}'".format(mode, return_string.decode('utf-8'))
            super().__init__(self.message)
    
    class IOError(Error):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)
        