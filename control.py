from lzfox import LZFOX
import datetime, pytz

if __name__ == '__main__':
    lzfox = LZFOX('/dev/ttyUSB0', '38400')
    #lzfox.connect()
    print("Connection: %s" % lzfox.checkConnection())
    # print("SET MODE: %s" % lzfox.setMode('CONTROL'))
    # print("CTRL: %s" % lzfox.setControl('FINISH'))
    # print("CTRL: %s" % lzfox.getCtrl())
    # print("SET MODE: %s" % lzfox.setMode('PRINT'))
    # print("Time: %s" % lzfox.getTime())
    # print("Mode: %s" % lzfox.getMode())
    # print("Version: %s" % lzfox.getVersion())
    # print("Voltage: %s" % lzfox.getVoltage())
    
    # #print("Backup: %s" % lzfox.getBackup("dump.txt"))


    # #print("SET MODE: %s" % lzfox.setMode('READOUT'))
    # print("SET TIME: %s" % lzfox.setTime(datetime.datetime.now(tz=pytz.utc)))
    # print("Time: %s" % lzfox.getTime())
    print("SET MODE: %s" % lzfox.setMode('WRITER'))
    print("WRITE INFO: %s" % lzfox.writeInfo("Lorem impsum"))