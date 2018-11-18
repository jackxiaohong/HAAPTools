# coding:utf-8

import ClassSW as sw
import ClassHAAP as haap
import Source as s
from collections import OrderedDict as Odd
from apscheduler.schedulers.blocking import BlockingScheduler
import os
import sys
import datetime
import getpass
import re
from mongoengine import *

from flask import Flask, render_template, redirect, request

try:
    import configparser as cp
except Exception:
    import ConfigParser as cp

# <<<Help String Feild>>>
strHelp = '''
        Command             Description

        -porterrshow      : Show PortError collected from SAN switches
        -clearporterrorAll: Clear ALL Ports' PortError Counter on SAN switches

        -getTrace         : Save engines' trace files under TraceFolder
        -analyseHAAP      : Analyze trace files under TraceFolder
        -analyseTrace     : Analyze trace files under <Folder>
        -CFGbackup        : Save engines' 'automap.cfg', 'cm.cfg', 'san.cfg' files to local 
        -autoCLI          : Execute commands listed in <File> on an <Engine>
        -pc               : Execute periodic-check commands on an <Engine>
        -pcALL            : Execute periodic-check commands on ALL Engines
        -updateFW         : Update an <Engine>'s firmware based on <Firmware_File>
        -healthHAAP       : Show health status (AH) for All engines
        -infoHAAP         : Show overall Info for All engines     
        -setTime          : Set date, day, and time as local time for All engines
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

strHelpUpdateFW = '''
    updateFW <Engine_IP> <Firmware_File>
'''

strHelpSingleCommand = '''
    {}
'''

# <<<Help String Field>>>


# <<<Read Config File Field>>>
objCFG = cp.ConfigParser(allow_no_value=True)
objCFG.read('Conf.ini')

# <<<DB Config>>>
strDBServer = objCFG.get('DBSetting', 'host')
intDBPort = int(objCFG.get('DBSetting', 'port'))
strDBName = objCFG.get('DBSetting', 'name')
# <<<DB Config>>>

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
    # t = s.TimeNow()
    # return '%s-%s-%s-%s-%s-%s' % (t.y(), t.mo(), t.d(),
    #                               t.h(), t.mi(), t.s())


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
        print("\nMirror Error")
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
    for i in lstIP:
        if _isIP(i):
            continue
        else:
            return False
    return True
# another way: return wrong IP(s) string ("" or "#wrongIps#")
#     wrong_IP = ""
#     for i in lstIP:
#         chk_pass = _isIP(i)
#         if chk_pass:
#             continue
#         else:
#             wrong_IP += i
#     return wrong_IP


def _isFile(s):
    if os.path.isfile(s):
        return True
    else:
        return False


def get_HAAP_status_list():
    lstHAAPstatus = []
    for i in lstHAAP:
        t = {}
        t[i] = _HAAP(i).infoEngine_lst()
        lstHAAPstatus.append(t)
    return lstHAAPstatus


class collHAAP(Document):
    time = DateTimeField(default=datetime.datetime.now())
    engine_status = ListField()


class DB_collHAAP(object):
    connect(strDBName, host=strDBServer, port=intDBPort)

    def haap_insert(self, lstSTS):
        t = collHAAP(engine_status=lstSTS)
        t.save()

    def haap_query(self, time_start, time_end):
        collHAAP.objects(date__gte=time_start,
                         date__lt=time_end).order_by('-date')

    def haap_list_all(self):
        for i in collHAAP.objects():
            print(i.time, i.engine_status)

    def get_last_record(self):
        last_record = collHAAP.objects().order_by('-time').first()
        print(last_record.time, last_record.engine_status)
        return(last_record.time, last_record.engine_status)


def timing_clct_to_db(intSec):
    t = s.Timing()
    db = DB_collHAAP()
    t.add_interval(db.haap_insert(get_HAAP_status_list()), inSec)
    print('update complately...')


def start_web():
    app = Flask(__name__, template_folder='./web/templates',
                static_folder='./web/static', static_url_path='')
    # basedir = os.path.abspath(os.path.dirname(__file__))
    # basedir = 'web'
    timing_clct_to_db(15)
    
    @app.route("/")
    def home():
        lstDesc = ('Engine', 'Uptime', 'AlertHold', 'FirmWare',
                   'Status', 'Master', 'Mirror')
        # lstStatus = []
        # for i in lstHAAP:
        #     lstStatus.append(_HAAP(i).infoEngine_lst())

        # lstHAAPstatus = get_HAAP_status_list()
        db = DB_collHAAP()
        last_update = db.get_last_record()
        lstStatus = []
        for i in lstHAAP:
            lstStatus.append(last_update.engine_status[i])
        # db.haap_insert(lstHAAPstatus)
        
        # print(lstStatus)



        return render_template("monitor.html",
                               Title=lstDesc,
                               Status=lstStatus,
                               refresh_time=_get_TimeNow())

    app.run(debug=True, host='0.0.0.0', port=5000)


# ################################################
# <<<Inside Function Field>>>


def main():
    if len(sys.argv) == 1:
        print(strHelp)

    elif sys.argv[1] == 'porterrshow':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('porterrshow'))
        elif not _checkIPlst(lstSW):
            print('IP error. Please check Switch IPs defined in "Conf.ini"')
        else:
            for i in range(len(lstSW)):
                _SW(lstSW[i], lstSWPorts[i]).show_porterrors()

    elif sys.argv[1] == 'clearporterrorAll':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('clearporterrorAll'))
        elif not _checkIPlst(lstSW):
            print('IP error. Please check Switch IPs defined in Conf.ini')
        else:
            for i in range(len(lstSW)):
                _SW(lstSW[i], lstSWPorts[i]).clear_porterr_All()

    # save engines' 'automap.cfg', 'cm.cfg', 'san.cfg' files to local
    elif sys.argv[1] == 'CFGbackup':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('CFGbackup'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strBackupFolder = '{}/{}'.format(strCFGFolder, _get_TimeNow())
            for i in lstHAAP:
                _get_HAAPInstance()[i].backup(strBackupFolder)

    # get engines' trace files under TraceFolder based on Trace levels
    elif sys.argv[1] == 'getTrace':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('getTrace'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strTraceFolder = '{}/{}'.format(strTCFolder, _get_TimeNow())
            # for i in lstHAAP:
            #     _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)
            for i in range(len(lstHAAP)):
                _HAAP(lstHAAP[i]).get_trace(strTraceFolder, intTLevel)

    elif sys.argv[1] == 'analyseHAAP':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('analyseHAAP'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strTraceFolder = '{}/{}'.format(strTCAFolder, _get_TimeNow())
            for i in lstHAAP:
                _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)
            _TraceAnalyse(strTraceFolder)

    elif sys.argv[1] == 'analyseTrace':
        if len(sys.argv) != 3:
            print(strHelpAnalyseTrace)
        elif isinstance(sys.argv[2], str):
            _TraceAnalyse(sys.argv[2])
        else:
            print('Please Provide Trace Folder To Analyse ...')

    elif sys.argv[1] == 'autoCLI':
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

    elif sys.argv[1] == 'updateFW':
        if len(sys.argv) != 4:
            print(strHelpUpdateFW)
        elif not _isIP(sys.argv[2]):
            print('IP format wrong. Please Provide Correct Engine IP...')
        elif not _isFile(sys.argv[3]):
            print('File Not exists. Please Provide Correct File...')
        else:
            _FWUpdate(sys.argv[2], sys.argv[3])

    elif sys.argv[1] == 'healthHAAP':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('healthHAAP'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            for i in lstHAAP:
                _EngineHealth(i)

    elif sys.argv[1] == 'infoHAAP':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('healthHAAP'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            _ShowEngineInfo()

    elif sys.argv[1] == 'setTime':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('setTime'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            for i in lstHAAP:
                engine = _get_HAAPInstance()[i]
                engine.set_engine_time()
#                 print("\n" + engine.get_engine_time())

    elif sys.argv[1] == 'test':
        start_web()

    else:
        print(strHelp)


if __name__ == '__main__':
    # a = DB_collHAAP()
    # a.insert([1,2,3])
    # print(a.list_all())
    # lstSTS = [1, 2, 3]
    # b = collHAAP(engine_status=lstSTS)
    # b.save

    # t = collHAAP(engine_status = [79,38])
    # t.save()
    m = DB_collHAAP()
    m.get_last_record()
    # m.haap_insert(['2dse4', '3saff'])
    # m.haap_list_all()
    # print(collHAAP.objects().all())
    # haap_insert([2323, 2323])
