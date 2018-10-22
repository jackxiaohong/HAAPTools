import ClassConnect
import re
import collections
from collections import OrderedDict
import os
import time
import Source as s


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
        try:
            self._telnet_Connection = ClassConnect.HAAPConn(self._host,
                                                            self._TNport,
                                                            self._password)
        except Exception as E:
            print('Connect to HAAP Engine Failed...')

    def _FTP_connect(self):
        try:
            self._FTP_Connection = ClassConnect.FTPConn(self._host,
                                                        self._FTPport,
                                                        'adminftp',
                                                        self._password)
        except Exception as E:
            print('Connect to HAAP Engine Failed...')

    @deco_Exception
    def get_vpd(self):
        if self._telnet_Connection:
            return self._telnet_Connection.ExecuteCommand('vpd')
        else:
            self._connect()
            return self._telnet_Connection.ExecuteCommand('vpd')

    @deco_Exception
    def get_engine_status(self):
        if self._telnet_Connection:
            strEnter = self._telnet_Connection.ExecuteCommand('')
        else:
            self._connect()
            strEnter = self._telnet_Connection.ExecuteCommand('')
        reCLI = re.compile(r'CLI>')
        if reCLI.search(strEnter):
            return "ONLINE"
        else:
            return "offline"

    def get_uptime(self, command="human"):
        strVPD_Info = self.get_vpd()
        reUpTime = re.compile(
            r'Uptime\s*:\s*((\d*)d*\s*(\d{2}):(\d{2}):(\d{2}))')
        result_reUptTime = reUpTime.search(strVPD_Info)

        if result_reUptTime is None:
            print("get uptime failed...")
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
            self._connect()
            strEngine_info = self._telnet_Connection.ExecuteCommand('engine')

        # make sure we can get engine info
        if re.search(r'>>', strEngine_info) is None:
            print("get engine info failed...")
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
            self._connect()
            return self._telnet_Connection.ExecuteCommand('mirror')

    def get_mirror_status(self):
        strMirror = self.get_mirror_info()
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
                return error_line
            else:
                return 0
        else:
            if reNoMirror.search(strMirror):
                print("No mirrors defined")
            else:
                print("get mirror status failed...")

    def get_version(self):
        strVPD_Info = self.get_vpd()
        reFirmware = re.compile(r'Firmware\sV\d+(.\d+)*')
        resultFW = reFirmware.search(strVPD_Info)
        if resultFW:
            return resultFW.group()
        else:
            print("get firmware version failed...")

    def backup(self, strBaseFolder):
        strOriginalFolder = os.getcwd()
        try:
            s.GotoFolder(strBaseFolder)
            connFTP = self._FTP_Connection
            lstCFGFile = ['automap.cfg', 'cm.cfg', 'san.cfg']
            for strCFGFile in lstCFGFile:
                connFTP.GetFile('bin_conf', '.', strCFGFile,
                                'backup_{}_{}'.format(self._host, strCFGFile))
                print('{} Backup Completely for {}'.format(
                    strCFGFile.ljust(12), self._host))
                time.sleep(1)
        except Exception as E:
            print(__name__, E)
            print('Config Backup Failed for {}'.format(self._host))
        finally:
            os.chdir(strOriginalFolder)

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
                time.sleep(0.5)
        except Exception as E:
            print(__name__, E)
        finally:
            os.chdir(strOriginalFolder)

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


if __name__ == '__main__':
    aa = HAAP('172.16.254.71', 23, '.com', 21)
    print(aa.get_vpd())
    print(os.getcwd())
    aa.backup('abc2/wdswe/')
    print(os.getcwd())

    #w = ClassConnect.FTPConn('172.16.254.71', 21, 'adminftp', '.com')

    # print(w.getwelcome())
