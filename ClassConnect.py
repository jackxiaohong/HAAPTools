# coding:utf-8

from ftplib import FTP
import paramiko
import telnetlib
import time


class FTPConn(object):
    def __init__(self, strIP, intPort, strUserName, strPasswd):
        self._host = strIP
        self._port = intPort
        self._username = strUserName
        self._password = strPasswd
        self._Connection = None
        self._connect()

    def _connect(self):
        ftp = FTP()
        def _conn():
            try:
                ftp.connect(self._host, self._port)
                return True
            except Exception as E:
                print('\nFTP Connect to {} Failed...\nReason: {}'.format(
                    self._host, E))
                return False

        def _login():
            try:
                ftp.login(self._username, self._password)
                return True
            except Exception as E:
                print('\nFTP Login to {} Failed...\nReason: {}'.format(
                    self._host, E))
                return False

        if _conn():
            if _login():
                self._Connection = ftp

    def GetFile(self, strRemoteFolder, strLocalFolder, strRemoteFileName,
                strLocalFileName, FTPtype='bin', intBufSize=1024):
        def _getfile():
            ftp = self._Connection
            # print(ftp.getwelcome())
            ftp.cwd(strRemoteFolder)
            objOpenLocalFile = open('{}/{}'.format(
                strLocalFolder, strLocalFileName), "wb")
            if FTPtype == 'bin':
                ftp.retrbinary('RETR {}'.format(strRemoteFileName),
                               objOpenLocalFile.write)
            elif FTPtype == 'asc':
                ftp.retrlines('RETR {}'.format(strRemoteFileName),
                              objOpenLocalFile.write)
            objOpenLocalFile.close()
            ftp.cwd('/')

        if self._Connection:
            _getfile()
        else:
            self._connect()
            try:
                _getfile()
            except Exception:
                print('Get File Failed...')

    def PutFile(self, strRemoteFolder, strLocalFolder, strRemoteFileName,
                strLocalFileName, FTPtype='bin', intBufSize=1024):
        def _putfile():
            ftp = self._Connection
            # print(ftp.getwelcome())
            ftp.cwd(strRemoteFolder)
            objOpenLocalFile = open('{}/{}'.format(
                strLocalFolder, strLocalFileName), 'rb')
            if FTPtype == 'bin':
                ftp.storbinary('STOR {}'.format(strRemoteFileName),
                               objOpenLocalFile, intBufSize)
            elif FTPtype == 'asc':
                ftp.storlines('STOR {}'.format(
                    strRemoteFileName), objOpenLocalFile)
            ftp.set_debuglevel(0)
            objOpenLocalFile.close()

        if self._Connection:
            _putfile()
        else:
            self._connect()
            try:
                _putfile()
            except Exception:
                print('Put File Failed...')
    
    def close(self):
        if self._Connection:
            self._Connection.quit()
            self._Connection = None


class SSHConn(object):
    def __init__(self, host, port, username, password, timeout):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self._client = None
        self._sftp = None
        self._connect()

    def _connect(self):
        def _make_connect():
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            self._client = objSSHClient
        try:
            _make_connect()
        except Exception as E:
            print(__name__, E)
            # try:
            #     _make_connect()
            # except Exception as E:
            #     pass
            # if not self._client:
            #     print('Can not connect to {}'.format(self._host))


    def download(self, remotepath, localpath):
        def _download():
            if self._sftp is None:
                self._sftp = self._client.open_sftp()
            self._sftp.get(remotepath, localpath)
        try:
            _download()
        except AttributeError as E:
            print(__name__, E)
            print('Download Failed,Not Connect to {}'.format(self._host))
            return None
        else:
            print(__name__, E)
            print('Download Failed ...')

    def upload(self, localpath, remotepath):
        def _upload():
            if self._sftp is None:
                self._sftp = self._client.open_sftp()
            self._sftp.put(localpath, remotepath)
        try:
            _upload()
        except AttributeError as E:
            print(__name__, E)
            print('Upload Failed,Not Connect to {}'.format(self._host))
            return None
        else:
            print(__name__, E)
            print('Upload Failed ...')

    def ExecuteCommand(self, command):
        def GetRusult():
            stdin, stdout, stderr = self._client.exec_command(command)
            data = stdout.read()
            if len(data) > 0:
                # print(data.strip())
                return data
            err = stderr.read()
            if len(err) > 0:
                print(err.strip())
                return err

        if self._client:
            return GetRusult()
        else:
            try:
                self._connect()
                return GetRusult()
            except Exception as E:
                print('Command {} Execute Failed...'.format(command))
                return None

    def close(self):
        if self._client:
            self._client.close()


class HAAPConn(object):
    def __init__(self, strIP, intPort, strPasswd):
        self._host = strIP
        self._port = intPort
        self._password = strPasswd
        self._strLoginPrompt = 'Enter password'
        self._strMainMenuPrompt = 'Coredump Menu'
        self._strCLIPrompt = 'CLI>'
        self._strCLIConflict = 'Another session owns the CLI'
        self._Connection = None
        self._connect()

    def _connect(self):
        try:
            objTelnetConnect = telnetlib.Telnet(self._host, self._port, timeout=5) #add timeout to avoid pending
            
            objTelnetConnect.read_until(
                self._strLoginPrompt.encode(encoding="utf-8"), timeout=2)
            objTelnetConnect.write(self._password.encode(encoding="utf-8"))
            objTelnetConnect.write(b'\r')
            objTelnetConnect.read_until(
                self._strMainMenuPrompt.encode(encoding="utf-8"), timeout=2)
            objTelnetConnect.write(b'7')
            
            strOutPut = objTelnetConnect.read_until(
                self._strCLIPrompt.encode(encoding="utf-8"), timeout=2)
            if int(strOutPut.find(self._strCLIPrompt.encode(
                    encoding="utf-8"))) > 0:
                self._Connection = objTelnetConnect
                time.sleep(0.25)
            elif int(strOutPut.find(self._strCLIConflict.encode(
                    encoding="utf-8"))) > 0:
                objTelnetConnect.write(b'y' + b'\r')
                strOutPut = objTelnetConnect.read_until(
                    self._strCLIPrompt.encode(encoding="utf-8"), timeout=2)
                if int(strOutPut.find(self._strCLIPrompt.encode(
                        encoding="utf-8"))) > 0:
                    self._Connection = objTelnetConnect
                    time.sleep(0.25)
            #                 print('''
            # ------Handle the CLI Succesfully For Engine: {}
            #                     '''.format(self._strIP))

        except Exception as E:
            return None
            print("------Goto CLI Failed For Engine: " + self._host, E)

    def ExecuteCommand(self, strCommand):

        CLI = self._strCLIPrompt.encode(encoding="utf-8")
        # CLI = self._strCLIPrompt
        CLI_Conflict = self._strCLIConflict.encode(encoding="utf-8")

        def GetResult():
            self._Connection.write(
                strCommand.encode(encoding="utf-8") + b'\r')
            strResult = str(self._Connection.read_until(
                CLI, timeout=3).decode())
            if self._strCLIPrompt in strResult:
                return strResult
            else:
                return None

        def FindCLI():
            self._Connection.write(b'\r')
            strEnterOutput = self._Connection.read_until(CLI, timeout=1)

            if CLI in strEnterOutput:
                return GetResult()
            elif 'HA-AP' in strEnterOutput:
                self._Connection.write('7')
                str7Output = self._Connection.read_until(CLI, timeout=1)
                if CLI in str7Output:
                    return GetResult()
                elif CLI_Conflict in str7Output:
                    self._Connection.write('y')
                    strConfirmCLI = self._Connection.read_until(CLI, timeout=1)
                    if CLI in strConfirmCLI:
                        return GetResult()

        if self._Connection:
            return FindCLI()
        else:
            self._connect()
            if self._Connection:
                return FindCLI()
            else:
                print('Connect Failed...')

    def Close(self):
        if self._Connection:
            self._Connection.close()


if __name__ == '__main__':
    aa = HAAPConn('172.16.254.71', 23, '.com')
    print(aa._Connection)
    # print(aa.ExecuteCommand('conmgr status'))
    # print(1)
    # time.sleep(3)
    # print(aa.ExecuteCommand('conmgr status'))
    # print(2)
    # time.sleep(3)
    # print(aa.ExecuteCommand('conmgr status'))
    # print(3)
    # time.sleep(3)
    # print(aa.ExecuteCommand('conmgr status'))
    # print(4)

    # lstCommand = ['vpd', 'conmgr status', 'mirror', 'explore b1']

    # for i in range(len(lstCommand)):
    #     result = aa.ExecuteCommand(lstCommand[i])
    #     if result:
    #         print result
    #         i += 1
    #     time.sleep(0.25)

    #bb = SSHConn('172.16.254.78', 22, 'admin', 'password', 5)
    # print(bb.ExecuteCommand('switchshow'))
    #bb.download('abc', 'def')