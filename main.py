# coding:utf-8
import ClassSW as sw
import ClassHAAP as haap
import Source as s
from collections import OrderedDict as Odd
import os
import sys
import datetime
import getpass
import pprint

try:
    import configparser as cp
except Exception:
    import ConfigParser as cp

# <<<Help String Feild>>>
strHelp = '''
        -run            : Run Normally
        -porterrshow    : Run, but Collect PortError only
        -statsclear     : Clear PortError Counter on the SAN Switch
        -zipall         : Zip All non-Zip File
        -check          : Run Periodic Check
        '''

strAutoCLIHelp = '''
    autoCLI <Engine_IP> <Command_File>
'''

strPCHelp = '''
    pc <Engine_IP>
'''

strHelpAnalyseTrace = '''
    analyseTrace <Trace_Folder>
'''
# <<<Help String Feild>>>


# <<<Read Config File Feild>>>
objCFG = cp.ConfigParser(allow_no_value=True)
objCFG.read('Conf.ini')
# <<<Read Config File Feild>>>


# <<<SAN Switch Config>>>
strSWUser = objCFG.get('SWSetting', 'username')
intSWSSHPort = objCFG.get('SWSetting', 'port')

oddSWPort = Odd()
for i in objCFG.items('SWPorts'):
    oddSWPort[i[0]] = eval(i[1])
lstSW = list(oddSWPort.keys())
lstSWPorts = list(oddSWPort.values())

strSWPWD = objCFG.get('SWSetting', 'password')
if strSWPWD:
    strSWPWD = strSWPWD
else:
    strSWPWD = getpass.getpass(
        prompt='Please Input Your SAN Switch Password for User {}:'.format(
            strSWUser), stream=None)
# <<<SAN Switch Config>>>


# <<<HAAP Config>>>
lstHAAP = list(i[0] for i in objCFG.items('Engines'))
intTLevel = int(objCFG.get('TraceSetting', 'TraceLevel'))
intTNPort = int(objCFG.get('EngineSetting', 'TelnetPort'))
intFTPPort = int(objCFG.get('EngineSetting', 'FTPPort'))
lstCheckCMD = list(i[0] for i in objCFG.items('PeriodicCheckCommand'))

strHAAPPasswd = objCFG.get('EngineSetting', 'HAAPPassword')
if strHAAPPasswd:
    strHAAPPasswd = strHAAPPasswd
else:
    strHAAPPasswd = getpass.getpass(
        prompt='Please Input Your Engine Password: ', stream=None)

oddHAAPErrorDict = Odd()
for i in objCFG.items('TraceRegular'):
    oddHAAPErrorDict[i[0]] = eval(i[1])
# <<<HAAP Config>>>


# <<<Folder Config>>>
# SWPEFolder = SAN Switch Port Error Folder
strSWPEFolder = objCFG.get('FolderSetting', 'swporterr')
# TCFolder = HAAP Get Trace Folder
strTCFolder = objCFG.get('FolderSetting', 'trace')
# TCAFolder = HAAP Trace Analyse Folder
strTCAFolder = objCFG.get('FolderSetting', 'traceanalyse')
# CFGFolder = HAAP Config Backup Folder
strCFGFolder = objCFG.get('FolderSetting', 'cfgbackup')
# PCFolder = HAAP Periodic Check Result Folder
strPCFolder = objCFG.get('FolderSetting', 'PeriodicCheck')
# <<<Folder Config>>>


# <<<Inside Function Feild>>>
# ################################################

def _get_TimeNow():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


# en-Instance The HAAP by IP...
def _HAAP(strEngineIP):
    return haap.HAAP(strEngineIP, intTNPort, strHAAPPasswd, intFTPPort)


# en-Instance The SAN Switch by IP and SAN Switch Ports...
def _SW(strSWIP, lstSWPorts):
    return sw.SANSW(strSWIP, intSWSSHPort,
                    strSWUser, strSWPWD, lstSWPorts)


# en-Instance All The SAN Switchs by IP and SAN Switch Ports...
def _get_SWInstance():
    oddSWInst = Odd()
    for i in range(len(lstSW)):
        oddSWInst[lstSW[i]] = _SW(lstSW[i], lstSWPorts[i])
    return oddSWInst


# en-Instance ALL The HAAPs in the config file by IP...
def _get_HAAPInstance():
    oddTNInst = Odd()
    for i in range(len(lstHAAP)):
        oddTNInst[lstHAAP[i]] = _HAAP(lstHAAP[i])
    return oddTNInst


def _TraceAnalyse(strDesFolder):
    s.TraceAnalyse(oddHAAPErrorDict, strDesFolder)


def _periodic_check(strEngineIP):
    _HAAP(strEngineIP).periodic_check(lstCheckCMD,
                                      strPCFolder,
                                      'PC_{}_{}.log'.format(
                                          _get_TimeNow(), strEngineIP))


def _AutoCLI(strEngineIP, CMDFile):
    _HAAP(strEngineIP).execute_multi_command(CMDFile)


def _FWUpdate(strEngineIP, strFWFile):
    _HAAP(strEngineIP).updateFW(strFWFile)
    

def _isIP(s):
    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(s):
        return True
    else:
        return False
    
def _isFile(s):
    if os.path.isfile(s):
        return True
    else: 
        return False

# ################################################
# <<<Inside Function Feild>>>


def main():
    if len(sys.argv) == 1:
        print(strHelp)

    elif sys.argv[1] == 'porterrshow':
        for i in lstSW:
            _get_SWInstance()[i].show_porterrors()

    elif sys.argv[1] == 'clearporterrorAll':
        for i in lstSW:
            _get_SWInstance()[i].clear_porterr_All()

    elif sys.argv[1] == 'CFGbackup':
        for i in lstHAAP:
            _get_HAAPInstance()[i].backup('{}/{}'.format(
                strCFGFolder, _get_TimeNow()))

    elif sys.argv[1] == 'getTrace':
        strTraceFolder = '{}/{}'.format(strTCFolder, _get_TimeNow())
        for i in lstHAAP:
            _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)

    elif sys.argv[1] == 'analyseHAAP':
        strTraceFolder = '{}/{}'.format(strTCAFolder, _get_TimeNow())
        for i in lstHAAP:
            _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)
        _TraceAnalyse(strTraceFolder)

    elif sys.argv[1] == 'analyseTrace':
        if len(sys.argv) != 2:
            print(strHelpAnalyseTrace)
        elif isinstance(sys.argv[1], str):
            _TraceAnalyse(sys.argv[1])
        else:
            print('Please Provide Trace Folder To Analyse ...')

    elif sys.argv[1] == 'autoCLI':
        if len(sys.argv) != 4:
            print(strAutoCLIHelp)
        else:
            _HAAP(sys.argv[2]).execute_multi_command(sys.argv[3])

    elif sys.argv[1] == 'pc':
        if len(sys.argv) != 3:
            print(strPCHelp)
        else:
            _periodic_check(sys.argv[2])

    elif sys.argv[1] == 'pcALL':
        for i in lstHAAP:
            _periodic_check(i)

    elif sys.argv[1] == 'updateFW':
        if len(sys.argv) != 4:
            print(strAutoCLIHelp)
        else:
            _FWUpdate(sys.argv[2], sys.argv[3])

    elif sys.argv[1] == 'test':
        print(len(sys.argv))
        
    else:
        print(strHelp)


if __name__ == '__main__':
    main()
