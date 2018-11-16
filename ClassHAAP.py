import ClassConnect
import re
from collections import OrderedDict
import os
import time
import Source as s


def deco_OutFromFolder(func):
    strOriFolder = os.getcwd()

    def _deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as E:
            print(func.__name__, E)
        finally:
            os.chdir(strOriFolder)
    return _deco


def deco_Exception(func):
    def _deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as E:
            print(func.__name__, E)
    return _deco


class HAAP():
    def __init__(self, strIP, intTNPort, strPassword,
                 intFTPPort, intTimeout=3):
        self._host = strIP
        self._TNport = intTNPort
        self._FTPport = intFTPPort
        self._password = strPassword
        self._timeout = intTimeout
        self._TN_Conn = None
        self._FTP_Conn = None
        self._telnet_connect()
        self._FTP_connect()

    def _telnet_connect(self):
        self._TN_Conn = ClassConnect.HAAPConn(self._host,
                                              self._TNport,
                                              self._password,
                                              self._timeout)

    def _FTP_connect(self):
        self._FTP_Conn = ClassConnect.FTPConn(self._host,
                                              self._FTPport,
                                              'adminftp',
                                              self._password,
                                              self._timeout)

    @deco_Exception
    def get_vpd(self):
        if self._TN_Conn:
            return self._TN_Conn.ExecuteCommand('vpd')
        else:
            self._telnet_connect()
            if self._TN_Conn:
                return self._TN_Conn.ExecuteCommand('vpd')

    def get_engine_status(self):
        if self._TN_Conn:
            strEngine = self._TN_Conn.ExecuteCommand('engine')
        else:
            self._telnet_connect()
            strEngine = self._TN_Conn.ExecuteCommand('engine')
        if strEngine is None:
            print "Get Online Status Failed for Engine {}".format("10.203.1.111")
        else:
            reCLI = re.compile(r'>>\s*\d*\s*(\(M\))*\s*Online')
            if reCLI.search(strEngine):
                return "ONLINE"
            else:
                return "offline"

    def get_engine_health(self):
        if self.get_engine_status()=="ONLINE":
            if self._TN_Conn:
                strEnter = self._TN_Conn.ExecuteCommand('')
            else:
                self._telnet_connect()
                strEnter = self._TN_Conn.ExecuteCommand('')
            if strEnter is None:
                print("Get Health Status Failed for Engine {}".format(self._host))
            else:
                reAL = re.compile('AH_CLI')
                if reAL.search(strEnter):
                    return 1 #1 means engine is not healthy (AH)
                else:
                    return 0 #0 means engine is healthy
            

    def get_uptime(self, command="human", strVPD_Info=None):
        if strVPD_Info is None:
            strVPD_Info = self.get_vpd()
        if strVPD_Info is None:
            print("Get Uptime Failed for Engine {}".format(self._host))
        else:
            reUpTime = re.compile(
                r'Uptime\s*:\s*((\d*)d*\s*(\d{2}):(\d{2}):(\d{2}))')
            result_reUptTime = reUpTime.search(strVPD_Info)

            if result_reUptTime is None:
                print("Get Uptime Failed for Engine {}".format(self._host))
            else:
                # return uptime in string
                if command == "human":
                    return result_reUptTime.group(1)

                # return day, hr, min, sec in list
                elif command == "list":
                    lsUpTime = []
                    # add day to list
                    try:
                        lsUpTime.append(int(result_reUptTime.group(2)))
                    except ValueError:
                        lsUpTime.append(0)
                    # add hr, min, sec to list
                    for i in range(3, 6):
                        lsUpTime.append(int(result_reUptTime.group(i)))
                    return lsUpTime

    @deco_Exception
    def is_master_engine(self):
        if self._TN_Conn:
            strEngine_info = self._TN_Conn.ExecuteCommand('engine')
        else:
            self._telnet_connect()
            strEngine_info = self._TN_Conn.ExecuteCommand('engine')

        if strEngine_info is None:
            print("Get Master Info Failed for Engine {}".format(self._host))
        else:
            if re.search(r'>>', strEngine_info) is None:
                print("Get Master Info Failed for Engine {}".format(self._host))
            else:
                # e.g. ">> 1  (M)" means current engine is master
                reMaster = re.compile(r'(>>)\s*\d*\s*(\(M\))')
                result_reMaster = reMaster.search(strEngine_info)
                if result_reMaster is None:
                    return False
                else:
                    return True

    @deco_Exception
    def get_mirror_info(self):
        if self._TN_Conn:
            return self._TN_Conn.ExecuteCommand('mirror')
        else:
            self._telnet_connect()
            return self._telnet_Connection.ExecuteCommand('mirror')

    @deco_Exception
    def get_mirror_status(self):
        strMirror = self.get_mirror_info()
        if strMirror is None:
            print("Get Mirror Status Failed for Engine {}".format(self._host))
        else:
            reMirrorID = re.compile(r'\s\d+\(0x\d+\)')  # e.g." 33281(0x8201)"
            reNoMirror = re.compile(r'No mirrors defined')

            if reMirrorID.search(strMirror):
                error_line = ""
                reMirrorStatus = re.compile(r'\d+\s\((\D*)\)')  # e.g."2 (OK )"
                lines = list(filter(None, strMirror.split("\n")))

                for line in lines:
                    if reMirrorID.match(line):
                        mirror_ok = True
                        mem_stat = reMirrorStatus.findall(line)
                        for status in mem_stat:
                            if status.strip() != 'OK':
                                mirror_ok = False
                        if not mirror_ok:
                            error_line += line + "\n"
                if error_line:
                    return error_line  # means mirror not okay
                else:
                    return 0  # 0 means mirror all okay
            else:
                if reNoMirror.search(strMirror):
                    return -1  # -1 means no mirror defined
                else:
                    print("Get Mirror Status Failed for Engine {}".format(self._host))

    @deco_Exception
    def get_version(self, strVPD_Info=None):
        if strVPD_Info is None:
            strVPD_Info = self.get_vpd()
        if strVPD_Info is None:
            print("Get Firmware Version Failed for Engine {}".format(self._host))

        else:
            reFirmware = re.compile(r'Firmware\sV\d+(.\d+)*')
            resultFW = reFirmware.search(strVPD_Info)
            if resultFW:
                return resultFW.group()
            else:
                print("Get Firmware Version Failed for Engine {}".format(self._host))

    @deco_OutFromFolder
    def backup(self, strBaseFolder):
        s.GotoFolder(strBaseFolder)
        connFTP = self._FTP_Conn
        lstCFGFile = ['automap.cfg', 'cm.cfg', 'san.cfg']
        for strCFGFile in lstCFGFile:
            if connFTP.GetFile('bin_conf', '.', strCFGFile,
                               'backup_{}_{}'.format(self._host, strCFGFile)):
                print('{} Backup Completely for {}'.format(
                    strCFGFile.ljust(12), self._host))
                continue
            else:
                break
            time.sleep(0.25)

    @deco_Exception
    def updateFW(self, strFWFile):
        FTPConn = self._FTP_Conn
        time.sleep(0.25)
        FTPConn.PutFile('/mbflash', './', 'fwimage', strFWFile)
        print('FW Upgrade Done for {}, Wait for reboot...'.format(
            self._host))

    @deco_Exception
    def execute_multi_command(self, strCMDFile):
        tn = self._TN_Conn
        with open(strCMDFile, 'r') as f:
            lstCMD = f.readlines()
            for strCMD in lstCMD:
                strResult = tn.ExecuteCommand(strCMD)
                if strResult:
                    print(strResult)
                else:
                    print('\rExecute Command "{}" Failed ...'.format(
                        strCMD))
                    break
                time.sleep(0.5)

    @deco_OutFromFolder
    def get_trace(self, strBaseFolder, intTraceLevel):
        tn = self._TN_Conn
        connFTP = self._FTP_Conn

        def _get_oddCommand(intTraceLevel):
            oddCMD = OrderedDict()
            if intTraceLevel == 1 or intTraceLevel == 2 or intTraceLevel == 3:
                oddCMD['Trace'] = 'ftpprep trace'
                if intTraceLevel == 2 or intTraceLevel == 3:
                    oddCMD['Primary'] = 'ftpprep coredump primary all'
                    if intTraceLevel == 3:
                        oddCMD['Secondary'] = 'ftpprep coredump secondary all'
                return oddCMD
            else:
                print('Trace Level: 1 or 2 or 3')

        def _get_trace_file(command, strTraceDes):
            # TraceDes = Trace Description
            def _get_trace_name():
                result = tn.ExecuteCommand(command)
                reTraceName = re.compile(r'(ftp_data_\d{8}_\d{6}.txt)')
                strTraceName = reTraceName.search(result)
                if strTraceName:
                    return strTraceName.group()
                else:
                    print('Generate Trace "{}" File Failed for {}'.format(
                        strTraceDes, self._host))
                    return None

            if _get_trace_name():
                time.sleep(0.2)
                strName = 'Trace_{}_{}.log'.format(self._host, strTraceDes)
                connFTP.GetFile('mbtrace', '.', _get_trace_name(), strName)
                print('Get Trace {:<10} for {} Completely ...'.format(
                    strTraceDes, self._host))
                return True
            else:
                s.ShowErrors('Can Not Get Trace Name...',
                             self.__class__.__name__)

        oddCommand = _get_oddCommand(intTraceLevel)
        lstCommand = list(oddCommand.values())
        lstDescribe = list(oddCommand.keys())

        s.GotoFolder(strBaseFolder)
        for i in range(len(lstDescribe)):
            try:
                _get_trace_file(lstCommand[i], lstDescribe[i])
                continue
            except Exception as E:
                # s.ShowErr(self.__class__.__name__,
                #           sys._getframe().f_code.co_name,
                #           'Get Trace "{}" Fail for Engine "{}",\
                # Error:'.format(
                #               lstDescribe[i], self._host),
                #           E)
                break
            time.sleep(0.1)

    @deco_OutFromFolder
    def periodic_check(self, lstCommand, strResultFolder, strResultFile):
        tn = self._TN_Conn
        s.GotoFolder(strResultFolder)
        with open(strResultFile, 'w') as f:
            if tn.ExecuteCommand('\n'):
                for strCMD in lstCommand:
                    time.sleep(0.5)
                    strResult = tn.ExecuteCommand(strCMD)
                    if strResult:
                        print(strResult)
                        f.write(strResult)
                    else:
                        strErr = '\n*** Execute Command "{}" Failed\n'.format(
                            strCMD)
                        # print(strErr)
                        f.write(strErr)
#             else:
#                 strMsg = '''
# ********************************************************************
# Error Message:
#     Connet Failed
#     Please Check Connection of Engine "{}" ...
# ********************************************************************'''.format(self._host)
#                 print(strMsg)
#                 f.write(strMsg)

    def infoEngine_lst(self):
        # return: [IP, uptime, AH, FM version, status, master, mirror status]
        strVPD = self.get_vpd()

        ip = self._host
        uptime = self.get_uptime(strVPD_Info=strVPD)
        ah = self.get_engine_health()
        if ah == 1:
            ah = "AH"
        elif ah == 0:
            ah = "None"

        version = self.get_version(strVPD_Info=strVPD)
        if version is not None:
            version = version[9:]

        status = self.get_engine_status()
        master = self.is_master_engine()
        if master is not None:
            if master:
                master = "M"
            else:
                master = ""

        mr_st = self.get_mirror_status()
        if mr_st == 0:
            mr_st = "All OK"
        elif mr_st == -1:
            mr_st = "No Mirror"
        else:
            if mr_st is not None:
                mr_st = "NOT ok"
        return [ip, uptime, ah, version, status, master, mr_st]

    def set_engine_time(self):
        def set_time():
            now = time.localtime()
            command_time = 'rtc set time {} {} {}'.format(
                now[3], now[4], now[5])
            r = self._telnet_Connection.ExecuteCommand(command_time)
            if r is None:
                print('Execute "rtc set time" failed for Engine "{}"'.format(self._host))
            else:
                print('Successfully Set Time for Engine "{}"'.format(self._host))
        if self._telnet_Connection:
            set_time()
        else:
            self._telnet_connect()
            set_time()

    def get_engine_time(self):
        if self._telnet_Connection:
            return self._telnet_Connection.ExecuteCommand('rtc')
        else:
            self._telnet_connect()
            return self._telnet_Connection.ExecuteCommand('rtc')


if __name__ == '__main__':
    aa = HAAP('10.203.1.111', 23, '', 21)
#     print(aa.get_vpd())
#     print(aa.get_uptime('list'))
#     a = HAAP('10.203.1.111', 23, '', 21)
    print aa.get_engine_health()
#     print a.get_engine_status()
#     print a.get_engine_health()
#     print a.get_uptime(command="human")
#     print a.is_master_engine()
#     print a.get_mirror_info()
#     print a.get_mirror_status()
#     print a.get_version()
#     print a.infoEngine_lst()

    # w = ClassConnect.FTPConn('172.16.254.71', 21, 'adminftp', '.com')

    # print(w.getwelcome())
    pass
