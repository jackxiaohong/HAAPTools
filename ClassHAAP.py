import ClassConnect
import re
import collections
from collections import OrderedDict
import os
import time
import Source as s
import sys


def deco_GotoFolder(func):
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

    # def self._telnet_connect(self):
    #     if self._FTP_Conn:
    #         return self._FTP_Conn
    #     else:
    #         if self._telnet_connect():
    #             return self._FTP_Conn
    #         else:
    #             print('FTP Connnect to {} Failed...'.format(self._host))
    #             return

    # def _make_TN_Conn(self):
    #     if self._TN_Conn:
    #         return self._TN_Conn
    #     else:
    #         if self._FTP_connect():
    #             return self._TN_Conn
    #         else:
    #             print('FTP Connnect to {} Failed...'.format(self._host))
    #             return

    def _telnetExcute(self, strCMD):
        return self._TN_Conn.ExecuteCommand(strCMD)

    # def _ShowErrors(strError,
    #                 className=self.__class__.__name__,
    #                 funcName=sys._getframe().f_code.co_name):
    #     return str('''
    # Errors:
    #     Class Name :   {}
    #     Function name: {}
    #     Error Message: {}
    #         '''.format(className, funcName, strError))

    @deco_Exception
    def get_vpd(self):
        if self._TN_Conn:
            return self._TN_Conn.ExecuteCommand('vpd')
        else:
            self._telnet_connect()
            if self._TN_Conn:
                return self._TN_Conn.ExecuteCommand('vpd')
            else:
                return

    @deco_Exception
    def get_engine_status(self):
        if self._TN_Conn:
            strEnter = self._TN_Conn.ExecuteCommand('')
        else:
            self._telnet_connect()
            strEnter = self._TN_Conn.ExecuteCommand('')
        reCLI = re.compile(r'CLI>')
        if reCLI.search(strEnter):
            return "ONLINE"
        else:
            return "offline"

    @deco_Exception
    def get_engine_health(self):
        # try:
        #     strVPD_Info = self.get_vpd()
        # except Exception as E:
        #     print(E)
        #     return

        strVPD_Info = self.get_vpd()
        reAL = re.compile(r'Alert:\s(\S*)')
        result_reAL = reAL.search(strVPD_Info)
        if result_reAL is None:
            print('get engine health status failed...')
        else:
            if result_reAL.group(1) == "None":
                return 0
            else:
                return 1

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
        if self._TN_Conn:
            strEngine_info = self._TN_Conn.ExecuteCommand('engine')
        else:
            self._telnet_connect()
            strEngine_info = self._TN_Conn.ExecuteCommand('engine')

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
        if self._TN_Conn:
            return self._TN_Conn.ExecuteCommand('mirror')
        else:
            if self._make_TN_Conn():
                return self._TN_Conn.ExecuteCommand('mirror')

    @deco_Exception
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

    @deco_Exception
    def get_version(self):
        strVPD_Info = self.get_vpd()
        reFirmware = re.compile(r'Firmware\sV\d+(.\d+)*')
        resultFW = reFirmware.search(strVPD_Info)
        if resultFW:
            return resultFW.group()
        else:
            print("get firmware version failed...")

    @deco_GotoFolder
    def backup(self, strBaseFolder):

        s.GotoFolder(strBaseFolder)
        connFTP = self._FTP_Conn
        lstCFGFile = ['automap.cfg', 'cm.cfg', 'san.cfg']
        for strCFGFile in lstCFGFile:
            connFTP.GetFile('bin_conf', '.', strCFGFile,
                            'backup_{}_{}'.format(self._host, strCFGFile))
            print('{} Backup Completely for {}'.format(
                strCFGFile.ljust(12), self._host))
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
                time.sleep(1)

    @deco_GotoFolder
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
            except Exception as E:
                s.ShowErr(self.__class__.__name__,
                          sys._getframe().f_code.co_name,
                          'Get Trace "{}" Fail for Engine "{}",Error:'.format(
                              lstDescribe[i], self._host),
                          E)
                continue
            # else:
            #     if self._telnet_connect():
            #         connFTP = self._FTP_Conn
            #         _get_trace_file(lstCommand[i], lstDescribe[i])
            #     else:
            #         print('FTP To {} Failed...'.format(self._host))
            #         continue

            # if tn:
            #     if connFTP:

            #     else:
            #         print('Please Check FTP Connection...')
            # else:
            #     print('Please Check Telnet Connection...')
            time.sleep(0.1)
        # print(os.listdir(strBaseFolder))
        # print(len(os.listdir(strBaseFolder)))
        # if len(os.listdir(strBaseFolder)) == 0:
        #     shutil.rmtree(strBaseFolder)

        # try:
        #     os.rmdir(strBaseFolder)
        #     print('No Trace File Got, Delete Folder {}'.format(strBaseFolder))
        # except OSError:
        #     pass

    @deco_GotoFolder
    def periodic_check(self, lstCommand, strResultFolder, strResultFile):
        tn = self._TN_Conn
        with open(strResultFile, 'w') as f:
            for strCMD in lstCommand:
                time.sleep(0.5)
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


if __name__ == '__main__':
    aa = HAAP('172.16.254.72', 23, '.com', 21)
    print(aa.get_vpd())
    print(aa.get_uptime('list'))

    #w = ClassConnect.FTPConn('172.16.254.71', 21, 'adminftp', '.com')

    # print(w.getwelcome())
