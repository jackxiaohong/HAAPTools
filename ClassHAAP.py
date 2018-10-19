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

    def get_engine_status(self):
        pass

    def get_uptime(self):
        strVPD_Info = self.get_vpd()
        reUpTime = re.compile(r'uptime')
        strUpTime = reUpTime.match(strVPD_Info)

        def list():
            pass

        def human():
            pass

    def is_master_engine(self):
        pass

    def get_mirror_info(self):
        pass

    def get_mirror_status(self):
        pass

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

    def execute_multi_command(self, strCMDFile):
        tnExecute = self._telnet_Connection.ExecuteCommand()
        with open(strCMDFile, 'r') as f:
            lstCommand = f.readlines()
            for i in range(len(lstCommand)):
                strResult = tnExecute(lstCommand[i])
                if strResult:
                    print(strResult)
                else:
                    print('\rExecute Command "{}" Failed...'.format(
                        lstCommand[i]))
                    break
                i += 1
                time.sleep(0.25)

    def get_trace(self, intTraceLevel, strBaseFolder):
        tn = self._telnet_Connection
        connFTP = self._FTP_Connection
        strOriginalFolder = os.getcwd()

        def _get_oddCommand(intTraceLevel):
            oddCommand = OrderedDict()
            if intTraceLevel == 1 or intTraceLevel == 2 or intTraceLevel == 3:
                oddCommand['Trace'] = 'ftpprep trace'
                if intTraceLevel == 2 or intTraceLevel == 3:
                    oddCommand['Primary'] = 'ftpprep coredump primary all'
                    if intTraceLevel == 3:
                        oddCommand['Secondary'] = 'ftpprep coredump secondary all'
                return oddCommand
            else:
                print('Error: Trace Level Must Be 1,2,3')
                return None

        def _get_trace_file(command, strTraceDes):

            def _get_trace_name():
                result = tn.ExecuteCommand(command)
                if result:
                    reTraceName = r'(ftp_data_\d{8}_\d{6}.txt)'
                    strTraceName = reTraceName.search(result)
                    if strTraceName:
                        return strTraceName
                    else:
                        print('Generate Trace File Failed...')
                        return None
                else:
                    print('Execute Command "{}" Failed...')
                    return None

            strTraceName = _get_trace_name(command)
            if strTraceName:
                try:
                    connFTP.GetFile('mbtrace', strTraceName, '.',
                                    'Trace_{}_{}.log'.format(strTraceDes,
                                                             self._host))
                    return True
                except Exception as E:
                    print('Get Trace File {} Failed...'.format(strTraceName))

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
        except Exception as E:
            print(__name__, E)
        finally:
            os.chdir(strOriginalFolder)

    def periodic_check(self, lstCommand, strResultFolder, strResultFile):
        tnExecute = self._telnet_Connection.ExecuteCommand()
        strOriginalFolder = os.getcwd()
        try:
            os.makedirs(strResultFolder)
        except OSError as E:
            pass
        os.chdir(strResultFolder)
        try:
            with open(strResultFile, 'w') as f:
                for i in range(len(lstCommand)):
                    strResult = tnExecute(lstCommand[i])
                    if strResult:
                        print(strResult)
                        f.write(strResult)
                    else:
                        print('\rExecute Command "{}" Failed...'.format(
                            lstCommand[i]))
                        break
                    i += 1
                    time.sleep(0.25)
        finally:
            os.chdir(strOriginalFolder)


if __name__ == '__main__':
    aa = HAAP('172.16.254.71', 23, '.com', 21)
    print(aa.get_vpd())
    print(os.getcwd())
    aa.backup('abc2/wdswe/')
    print(os.getcwd())

    #w = ClassConnect.FTPConn('172.16.254.71', 21, 'adminftp', '.com')

    #print(w.getwelcome())