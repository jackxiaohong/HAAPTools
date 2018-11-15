import ClassConnect
import re
import collections
from collections import OrderedDict
import os
import time
import Source as s
import datetime


strOriFolder = os.getcwd()
def deco_GotoFolder(strOriFolder):
    def _deco(func):
        def __deco(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as E:
                print(__name__, E)
            finally:
                os.chdir(strOriFolder)
        return __deco
    return _deco


def deco_Exception(func):
    def _deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as E:
            print(__name__, E)
            print('Please Check HAAP connection...')
    return _deco


class HAAP():
    def __init__(self, strIP, intTNPort, strPassword,
                 intFTPPort, intTimeout=5):
        self._host = strIP
        self._TNport = intTNPort
        self._FTPport = intFTPPort
        self._password = strPassword
        self._timeout = intTimeout
        self._telnet_Connection = None
        self._FTP_Connection = None
        self._telnet_connect()
        self._FTP_connect()

    def _telnet_connect(self):
        self._telnet_Connection = ClassConnect.HAAPConn(self._host,
                                                self._TNport,
                                                self._password)

    def _FTP_connect(self):
        self._FTP_Connection = ClassConnect.FTPConn(self._host,
                                                                self._FTPport,
                                                                'adminftp',
                                                                self._password)

    @deco_Exception
    def get_vpd(self):
        if self._telnet_Connection:
            return self._telnet_Connection.ExecuteCommand('vpd') #None to result string
        else:
            self._telnet_connect()
            return self._telnet_Connection.ExecuteCommand('vpd') #None to result string

    def get_engine_status(self):
        if self._telnet_Connection:
            strEnter = self._telnet_Connection.ExecuteCommand('')
        else:
            self._telnet_connect()
            strEnter = self._telnet_Connection.ExecuteCommand('')
        if strEnter is None:
            print("Get Status Failed for Engine {}".format(self._host))
        else:
            reCLI = re.compile(r'CLI>')
            if reCLI.search(strEnter):
                return "ONLINE"
            else:
                return "offline"
    
    def get_engine_health(self, strVPD_Info=None):
        if strVPD_Info is None:
            strVPD_Info = self.get_vpd()
        if strVPD_Info is None:
            print("Get Health Status Failed for Engine {}".format(self._host))
        else:            
            reAL = re.compile(r'Alert:\s(\S*)')
            result_reAL = reAL.search(strVPD_Info)
            if result_reAL is None:
                print("Get Health Status Failed for Engine {}".format(self._host))
            else:
                if result_reAL.group(1) == "None":
                    return 0 # 0 means engine is healthy
                else:
                    return 1 # 1 means engine has AH

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
        if self._telnet_Connection:
            strEngine_info = self._telnet_Connection.ExecuteCommand('engine')
        else:
            self._telnet_connect()
            strEngine_info = self._telnet_Connection.ExecuteCommand('engine')

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
        if self._telnet_Connection:
            return self._telnet_Connection.ExecuteCommand('mirror')
        else:
            self._telnet_connect()
            return self._telnet_Connection.ExecuteCommand('mirror')

    def get_mirror_status(self, strMirror=None):
        if strMirror is None:
            strMirror = self.get_mirror_info()
        if strMirror is None:
            print ("Get Mirror Status Failed for Engine {}".format(self._host))
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
                    return error_line # means mirror not okay
                else:
                    return 0 #0 means mirror all okay
            else:
                if reNoMirror.search(strMirror):
                    return -1 #-1 means no mirror defined
                else:
                    print("Get Mirror Status Failed for Engine {}".format(self._host))

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

    @deco_GotoFolder(strOriFolder)
    def backup(self, strBaseFolder):
        s.GotoFolder(strBaseFolder)
        connFTP = self._FTP_Connection
        lstCFGFile = ['automap.cfg', 'cm.cfg', 'san.cfg']
        for strCFGFile in lstCFGFile:
            connFTP.GetFile('bin_conf', '.', strCFGFile,
                            'backup_{}_{}'.format(self._host, strCFGFile))
            print('{} Backup Completely for {}'.format(
                strCFGFile.ljust(12), self._host))
            time.sleep(0.25)

    def updateFW(self, strFWFile):
        FTPConn = self._FTP_Connection
        try:
            time.sleep(1)
            FTPConn.PutFile('/mbflash', './', 'fwimage', strFWFile)
            return True
        except Exception as E:
            print(__name__, E)
            print('FW Update Failed for Engine {}...'.format(self._host))
            return False

    def execute_multi_command(self, strCMDFile):
        tn = self._telnet_Connection
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
                time.sleep(1)

    def get_trace(self, strBaseFolder, intTraceLevel):
        tn = self._telnet_Connection
        connFTP = self._FTP_Connection
        strOriginalFolder = os.getcwd()

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
                print('Error: Trace Level Must Be 1,2,3')
                return None

        def _get_trace_file(command, strTraceDes):
            # TraceDes = Trace Description
            def _get_trace_name():
                result = tn.ExecuteCommand(command)
                if result:
                    reTraceName = re.compile(r'(ftp_data_\d{8}_\d{6}.txt)')
                    strTraceName = reTraceName.search(result)
                    if strTraceName:
                        return strTraceName.group()
                    else:
                        print('Generate Trace "{}" File Failed for {}'.format(
                            strTraceDes, self._host))
                        return None
                else:
                    print('Execute Command "{}" Failed...'.format(command))
                    return None

            strTraceName = _get_trace_name()
            if strTraceName:
                try:
                    connFTP.GetFile('mbtrace', '.', strTraceName,
                                    'Trace_{}_{}.log'.format(
                                        self._host, strTraceDes))
                    print('Get Trace {} for Engine {} Completely ...'.format(
                        '"{}"'.format(strTraceDes).ljust(10), self._host))
                    return True
                except Exception as E:
                    print('Get Trace File {} Failed ...'.format(strTraceName))

        oddCommand = _get_oddCommand(intTraceLevel)
        lstCommand = list(oddCommand.values())
        lstDescribe = list(oddCommand.keys())

        try:
            s.GotoFolder(strBaseFolder)
            for i in range(len(lstDescribe)):
                if not tn:
                    self._telnet_connect()
                if not connFTP:
                    self._FTP_connect()
                _get_trace_file(lstCommand[i], lstDescribe[i])
                print('get trace of ' + self._host + '@' + os.getcwd())
                time.sleep(0.5)
        except Exception as E:
            print(__name__, E)
        finally:
            os.chdir(strOriginalFolder)
            print('get trace completely ' + self._host + '@' + os.getcwd())

    def periodic_check(self, lstCommand, strResultFolder, strResultFile):
        tn = self._telnet_Connection
        strOriginalFolder = os.getcwd()

        try:
            s.GotoFolder(strResultFolder)
            with open(strResultFile, 'w') as f:
                for strCMD in lstCommand:
                    time.sleep(1)
                    strResult = tn.ExecuteCommand(strCMD)
                    if strResult:
                        print(strResult)
                        f.write(strResult)
                    else:
                        strErr = '\n*** Execute Command "{}" Failed\n'.format(
                            strCMD)
                        print(strErr)
                        f.write(strErr)
                        continue
        finally:
            os.chdir(strOriginalFolder)
            
    def infoEngine_lst(self):
        #return: [IP, uptime, AH, FM version, status, master, mirror status]
        strVPD = self.get_vpd()
       
        ip = self._host
        uptime = self.get_uptime(strVPD_Info=strVPD)
        ah = self.get_engine_health(strVPD_Info=strVPD)
        if ah == 1: 
            ah = "AH"
        elif ah == 0: 
            ah = "None"
        
        version = self.get_version(strVPD_Info=strVPD)
        if version is not None: version = version[9:]
        
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
        def check_response(actual_response, cmd_line):
            if actual_response is None:
                return False
            else:
                return True
            # More checks needs here
#                 if actual_response == correct_response.format(cmd_line):
#                     return True
#                 else:
#                     return False 
            
        def set_time():
            now = datetime.datetime.now()
            y = now.year
            m = now.month
            d = now.day
            hr = now.hour
            min = now.minute
            sec = now.second
            weekday = now.isoweekday()+1
            if weekday>7: weekday=1
            
            command_date = 'rtc set date {} {} {}'.format(m, d, y-2000)
            r1 = self._telnet_Connection.ExecuteCommand(command_date)
            if not check_response(r1, command_date):
                print('Execute "rtc set date" failed for Engine "{}"'.format(self._host))
            
            command_time = 'rtc set time {} {} {}'.format(hr, min, sec)
            r2 = self._telnet_Connection.ExecuteCommand(command_time)
            if not check_response(r2, command_time):
                print('Execute "rtc set time" failed for Engine "{}"'.format(self._host))
           
            command_day = 'rtc set day {}'.format(weekday)
            r3 = self._telnet_Connection.ExecuteCommand(command_day)
            if not check_response(r3, command_day):
                print('Execute "rtc set day" failed for Engine "{}"'.format(self._host))
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
    aa.set_engine_time()
#     print a.get_engine_status()
#     print a.get_engine_health()
#     print a.get_uptime(command="human")
#     print a.is_master_engine()
#     print a.get_mirror_info()
#     print a.get_mirror_status()
#     print a.get_version()
#     print a.infoEngine_lst()
    
    
    #w = ClassConnect.FTPConn('172.16.254.71', 21, 'adminftp', '.com')

    # print(w.getwelcome())
