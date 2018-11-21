# coding:utf-8

import ClassSW as sw
import ClassHAAP as haap
import Source as s
from collections import OrderedDict as Odd
import os
import sys
import datetime
import getpass
import re

try:
    import configparser as cp
except Exception:
    import ConfigParser as cp

# <<<Help String Feild>>>
strHelp = '''
        Command           Description

        ptes           : Print Port Error of Defined SAN Switch Ports
        ptcl           : Clear Port Error Counter for Given Port on Given SAN switch
        ptclALL        : Clear Port Error Counter for All Ports on All Defined SAN switches
        sws            : Print switchshow Info for Given SAN Switch
        swsALL         : Print switchshow Info for All Defined SAN Switches
        gt             : Get Trace of All Defined Engine, Save in {trace} Folder
        anls           : Analyse Trace of All Defined Engine
        anlsTrace      : Analyze Trace Files under <Folder>
        bkCFG          : Backup Config for All Defined Engines, Save in {cfg} Folder
        ec             : Execute Commands listed in <File> on Given Engine
        pc             : Execute Periodic Check on Given Engine, Save in {pc} Folder
        pcALL          : Execute Periodic Check on All Defined Engine, Save in {pc} Folder
        chgFW          : Change Firmware for Given Engine
        sts            : Show Overall Status for All Engines
        st             : Sync Time with Local System For All Engines       
        '''

strPTCLHelp = '''
    ptcl <Switch_IP> <Port_Num>
'''

strSWSHelp = '''
    sws <Switch_IP> 
'''

strAutoCLIHelp = '''
    ec <Engine_IP> <Command_File>
'''

strPCHelp = '''
    pc <Engine_IP>
'''

strHelpAnalyseTrace = '''
    anlsTrace <Trace_Folder>
'''

strHelpUpdateFW = '''
    chgFW <Engine_IP> <Firmware_File>
'''

strHelpSingleCommand = '''
    {}
'''

# <<<Help String Field>>>


# <<<Read Config File Field>>>
objCFG = cp.ConfigParser(allow_no_value=True)
objCFG.read('Conf.ini')


# <<<SAN Switch Config>>>
strSWUser = objCFG.get('SWSetting', 'username')
intSWSSHPort = int(objCFG.get('SWSetting', 'port'))

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
# <<<Read Config File Field>>>

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
        oddSWInst[lstSW[i]] = sw.SANSW(lstSW[i], intSWSSHPort,
                                       strSWUser, strSWPWD, lstSWPorts[i])
    return oddSWInst


def _sw_switchshow(strSWIP):
    _SW(strSWIP, [])._switchshow()

# en-Instance ALL The HAAPs in the config file by IP...


def _get_HAAPInstance():
    oddTNInst = Odd()
    for i in range(len(lstHAAP)):
        oddTNInst[lstHAAP[i]] = _HAAP(lstHAAP[i])
    return oddTNInst

# analyze trace files under DesFolder, results saved in .xsl files


def _TraceAnalyse(strDesFolder):
    s.TraceAnalyse(oddHAAPErrorDict, strDesFolder)

# execute periodic-check commands (defined in Config.ini),\
# print and save results in PCFolder


def _periodic_check(strEngineIP):
    _HAAP(strEngineIP).periodic_check(lstCheckCMD,
                                      strPCFolder,
                                      'PC_{}_{}.log'.format(
                                          _get_TimeNow(), strEngineIP))


# execute cmds in file and print the results
def _AutoCLI(strEngineIP, CMDFile):
    _HAAP(strEngineIP).execute_multi_command(CMDFile)


def _FWUpdate(strEngineIP, strFWFile):
    _HAAP(strEngineIP).updateFW(strFWFile)


def _EngineHealth(strEngineIP):
    alert = _HAAP(strEngineIP).get_engine_health()
    if alert is not None:
        if alert:
            al_st = "AH"
        else:
            al_st = "OK"
        print("{}: {}".format(strEngineIP, al_st))

# def _ShowEngineInfo(strEngineIP):
#     engineIns = _HAAP(strEngineIP)
#     print "{:<17s}:".format("Engine IP"), strEngineIP
#     print "{:<17s}:".format("Status"), engineIns.get_engine_status()
#     print "{:<17s}:".format("Firmware version"), engineIns.get_version()
#     print "{:<17s}:".format("Uptime"), engineIns.get_uptime()
#
#     if engineIns.get_engine_health():
#         print "{:<17s}: AH".format("Alert Halt")
#     else:
#         print "{:<17s}: None".format("Alert Halt")
#
#     if engineIns.is_master_engine():
#         print "{:<17s}: Yes".format("Master")
#     else:
#         print "{:<17s}: No".format("Master")
#
#     mirror_status = engineIns.get_mirror_status()
#     if mirror_status == 0:
#         print "{:<17s}: All OK\n".format("Mirror status")
#     else:
#         print "{:<17s}: \n".format("Mirror status"), mirror_status, "\n"


def _ShowEngineInfo():
    dictEngines = _get_HAAPInstance()
    info_lst = []
    for i in lstHAAP:
        info_lst.append(dictEngines[i].infoEngine_lst())

    def general_info():
        lstDesc = ('EngineIP', 'Uptime', 'AH', 'Firm_Version',
                   'Status', 'Master', 'Mirror')
        for strDesc in lstDesc:
            print(strDesc.center(14)),
        print
        for i in info_lst:
            for s in i:
                if s is not None:
                    print(s.center(14)),
                else:
                    print("None".center(14)),
            print

    def mirror_info():  # needs optimization
        print "\nMirror Error"
        for i in lstHAAP:
            print i, ":",
            mirror_status = dictEngines[i].get_mirror_status()
            if mirror_status != 0 and mirror_status != -1:
                print mirror_status
            else:
                print "None"
    general_info()
    mirror_info()


def _isIP(s):
    p = re.compile(
        '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if p.match(s):
        return True
    else:
        return False


def _checkIPlst(lstIP):
    return all(map(_isIP, lstIP))


def _isFile(s):
    if os.path.isfile(s):
        return True
    else:
        return False


def _isPort(s):
    if type(s) == int:
        return True
    if type(s) == str:
        if s.isdigit():
            if type(eval(s)) == int:
                return True
    return False
# ################################################
# <<<Inside Function Field>>>


def main():
    if len(sys.argv) == 1:
        print(strHelp)

    elif sys.argv[1] == 'ptes':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('ptes'))
        elif not _checkIPlst(lstSW):
            print('IP error. Please check Switch IPs defined in "Conf.ini"')
        else:
            for i in range(len(lstSW)):
                _SW(lstSW[i], lstSWPorts[i]).show_porterrors()

    elif sys.argv[1] == 'ptcl':
        if len(sys.argv) != 4:
            print(strPTCLHelp)
        elif not _isIP(sys.argv[2]):
            print('IP Format Wrong. Please Provide Correct Switch IP...')
        elif not _isPort(sys.argv[3]):
            print('Switch Port Format Wrong. Please Provide Correct Port Number...')
        else:
            _SW(sys.argv[2], [int(sys.argv[3])]
                ).clear_porterr_by_port(int(sys.argv[3]))

    elif sys.argv[1] == 'ptclALL':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('ptclALL'))
        elif not _checkIPlst(lstSW):
            print('IP error. Please check Switch IPs defined in Conf.ini')
        else:
            for i in range(len(lstSW)):
                _SW(lstSW[i], lstSWPorts[i]).clear_porterr_All()

    elif sys.argv[1] == 'sws':
        if len(sys.argv) != 3:
            print(strSWSHelp)
        elif not _isIP(sys.argv[2]):
            print('IP Format Wrong. Please Provide Correct Switch IP...')
        else:
            _SW(sys.argv[2], [])._switchshow()  # no ports needed

    elif sys.argv[1] == 'swsALL':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('swsALL'))
        elif not _checkIPlst(lstSW):
            print('IP error. Please check Switch IPs defined in Conf.ini')
        else:
            for i in range(len(lstSW)):
                _SW(lstSW[i], lstSWPorts[i])._switchshow()

    # save engines' 'automap.cfg', 'cm.cfg', 'san.cfg' files to local
    elif sys.argv[1] == 'bkCFG':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('bkCFG'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strBackupFolder = '{}/{}'.format(strCFGFolder, _get_TimeNow())
            for i in lstHAAP:
                _get_HAAPInstance()[i].backup(strBackupFolder)

    # get engines' trace files under TraceFolder based on Trace levels
    elif sys.argv[1] == 'gt':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('gt'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strTraceFolder = '{}/{}'.format(strTCFolder, _get_TimeNow())
            # for i in lstHAAP:
            #     _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)
            for i in range(len(lstHAAP)):
                _HAAP(lstHAAP[i]).get_trace(strTraceFolder, intTLevel)

    elif sys.argv[1] == 'anls':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('anls'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strTraceFolder = '{}/{}'.format(strTCAFolder, _get_TimeNow())
            for i in lstHAAP:
                _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)
            _TraceAnalyse(strTraceFolder)

    elif sys.argv[1] == 'anlsTrace':
        if len(sys.argv) != 3:
            print(strHelpAnalyseTrace)
        elif isinstance(sys.argv[2], str):
            _TraceAnalyse(sys.argv[2])
        else:
            print('Please Provide Trace Folder To Analyse ...')

    elif sys.argv[1] == 'ec':
        if len(sys.argv) != 4:
            print(strAutoCLIHelp)
        elif not _isIP(sys.argv[2]):
            print('IP Format Wrong. Please Provide Correct Engine IP...')
        elif not _isFile(sys.argv[3]):
            print('File Not Exists. Please Provide Correct File...')
        else:
            _HAAP(sys.argv[2]).execute_multi_command(sys.argv[3])

    elif sys.argv[1] == 'pc':
        if len(sys.argv) != 3:
            print(strPCHelp)
        elif not _isIP(sys.argv[2]):
            print('IP Format Wrong. Please Provide Correct Engine IP...')
        else:
            _periodic_check(sys.argv[2])

    elif sys.argv[1] == 'pcALL':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('pcALL'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            for i in lstHAAP:
                _periodic_check(i)

    elif sys.argv[1] == 'chgFW':
        if len(sys.argv) != 4:
            print(strHelpUpdateFW)
        elif not _isIP(sys.argv[2]):
            print('IP format wrong. Please Provide Correct Engine IP...')
        elif not _isFile(sys.argv[3]):
            print('File Not exists. Please Provide Correct File...')
        else:
            _FWUpdate(sys.argv[2], sys.argv[3])

#     elif sys.argv[1] == 'healthHAAP':
#         if len(sys.argv) != 2:
#             print(strHelpSingleCommand.format('healthHAAP'))
#         elif not _checkIPlst(lstHAAP):
#             print('IP error. Please check Engine IPs defined in Conf.ini')
#         else:
#             for i in lstHAAP:
#                 _EngineHealth(i)

    elif sys.argv[1] == 'sts':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('sts'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            _ShowEngineInfo()

    elif sys.argv[1] == 'st':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('st'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            for i in lstHAAP:
                engine = _HAAP(i)
                engine.set_engine_time()
                print("\n" + engine.get_engine_time())

    elif sys.argv[1] == 'test':
        _SW(sys.argv[2], [])._switchshow()

    else:
        print(strHelp)


if __name__ == '__main__':
    main()
