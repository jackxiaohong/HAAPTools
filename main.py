# coding:utf-8
from __future__ import print_function
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
from threading import Thread
import thread

from flask import Flask, render_template, redirect, request

try:
    import configparser as cp
except Exception:
    import ConfigParser as cp

import logging
logging.basicConfig()

# <<<Help String Feild>>>
strHelp = '''
        Command           Description

        ptes           : Print Port Error of Defined SAN Switch Ports
        ptcl           : Clear Port Error Counter for Given Port on Given SAN switch
        ptclALL        : Clear Port Error Counter for All Ports on All Defined SAN switches
        sws            : Print switchshow Info for Given SAN Switch
        swsALL         : Print switchshow Info for All Defined SAN Switches
        gt             : Get Trace of All Defined Engine(s), Save in {trace} Folder
        anls           : Analyse Trace of All Defined Engine(s)
        anlsTrace      : Analyze Trace Files under <Folder>
        bkCFG          : Backup Config for All Defined Engine(s), Save in {cfg} Folder
        ec             : Execute Commands listed in <File> on Given Engine
        pc             : Execute Periodic Check on Given Engine, Save in {pc} Folder
        pcALL          : Execute Periodic Check on All Defined Engine(s), Save in {pc} Folder
        chgFW          : Change Firmware for Given Engine
        sts            : Show Overall Status for All Engines
        st             : Sync Time with Local System For All Engines
        stm            : Get Time of All Defined Engine(s)
        wrt            : Start Web Update Real Time
        wdb            : Start Web Update from DataBase
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

# 调用config文件，数据库的端口路径
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
print (lstSW)
lstSWPorts = list(oddSWPort.values())
print (lstSWPorts)

strSWPWD = objCFG.get('SWSetting', 'password')
if strSWPWD:
    strSWPWD = strSWPWD
else:
    strSWPWD = getpass.getpass(
        prompt='Please Input Your SAN Switch Password for User {}:'.format(
            strSWUser), stream=None)
    
# 获取交换机的Ip
# <<<SAN Switch Config>>>
addSwitches = Odd()
for i in objCFG.items('Switches'):
    addSwitches[i[0]] = i[1]
lstSwitchAlias = list(addSwitches.keys())
lstSwitch = list(addSwitches.values())

# <<<HAAP Config>>>
oddEngines = Odd()
for i in objCFG.items('Engines'):
    oddEngines[i[0]] = i[1]
lstHAAPAlias = list(oddEngines.keys())
lstHAAP = list(oddEngines.values())
# lstHAAP = list(i[0] for i in objCFG.items('Engines'))
intTLevel = int(objCFG.get('MessageLogging', 'TraceLevel'))
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


# 方法
def _get_TimeNow_Human():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _get_TimeNow_Folder():
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


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
                                          _get_TimeNow_Folder(), strEngineIP))


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
            print(strDesc.center(14), end=''),
        print()
        for i in info_lst:
            for s in i:
                if s is not None:
                    print(s.center(14), end=''),
                else:
                    print("None".center(14), end=''),
            print()

    def mirror_info():  # needs optimization
        print("\nMirror Error")
        for i in lstHAAP:
            print(i, ":")
            mirror_status = dictEngines[i].get_mirror_status()
            if mirror_status != 0 and mirror_status != -1:
                print(mirror_status)
            else:
                print("None")

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


# engine数据获取方法
def get_HAAP_status_list():
    lstHAAPstatus = []
    for i in range(len(lstHAAP)):
        t = {}
        t[lstHAAPAlias[i]] = _HAAP(lstHAAP[i]).infoEngine_lst()
        lstHAAPstatus.append(t)
        # print ("#####################:", lstHAAPstatus)
    return lstHAAPstatus

# Switch数据获取方法
'''def get_Switch_status_list():
    lstSwitchstatus = []
    for i in range(len(lstSW)):
        a = {}
        a[lstSwitchAlias[i]] = _SW(lstSW[i],lstSWPorts)._dicPartPortError[1]
        lstSwitchstatus.append(a)

        #print("444444444444:",_dicPartPortError)
        print ("###222222222222222########:", lstSwitchstatus)
    return lstSwitchstatus'''


def get_Switch_status_list():
    lstSwitchstatus = {}
    ENCOUT = []
    DICT3 = []
    for i in range(len(lstSW)): 
        encout = 0
        dict3 = 0
        a = {}
        c = {} 
        d = {}
        for h in range(len(lstSWPorts[i])):
           # print("h:", lstSWPorts[i][h]) 
            q = lstSWPorts[i][h]
            # print ('aaaa',q)
            b = _SW(lstSW[i], lstSWPorts[i])._dicPartPortError[q]
            # print('dasdssdfsdfsdf',b[2][:-1])
            if b[2][-1] == 'm' or b[2][-1] == 'k':
                if b[2][-1] == 'm':
                    b[2] = (float(b[2][0:-1])) * 10000
                else:
                    b[2] = (float(b[2][0:-1])) * 1000
            encout += int(b[2])

            if b[3][-1] == 'm' or b[3][-1] == 'k':
                if b[3][-1] == 'm':
                    b[3] = (float(b[3][0:-1])) * 10000
                else:
                    b[3] = (float(b[3][0:-1])) * 1000
            dict3 += int(b[3]) 
            a['port' + str(lstSWPorts[i][h])] = b
 
        a['IP'] = lstSW[i]

        s = str(lstSW[i]) + ':' + ' '
        s += str(encout)
        s2 = str(lstSW[i]) + ':' + ' '
        s2 += str(dict3)
        ENCOUT.append(s)
        DICT3.append(s2)

        lstSwitchstatus[str(i)] = (a)
        lstSwitchstatus.update(ENCOUT=ENCOUT)
        lstSwitchstatus.update(DISCC3=DICT3)
    return lstSwitchstatus

# <<get SW Warning>>
def get_Switch_warning():
    for i in range(len(lstSW)): 
        encoutw = 0
        discc3w = 0
        for h in range(len(lstSWPorts[i])):
            #print("h:", lstSWPorts[i][h]) 
            q = lstSWPorts[i][h]
            # print ('aaaa',q)
            b = _SW(lstSW[i], lstSWPorts[i])._dicPartPortError[q]
            #print('nnnnnn',b,lstSW,lstSW[i])
            # print('dasdssdfsdfsdf',b[2][:-1])
            if b[2][-1] == 'm' or b[2][-1] == 'k':
                if b[2][-1] == 'm':
                    b[2] = (float(b[2][0:-1])) * 10000
                else:
                    b[2] = (float(b[2][0:-1])) * 1000
            encoutw += int(b[2])

            if b[3][-1] == 'm' or b[3][-1] == 'k':
                if b[3][-1] == 'm':
                    b[3] = (float(b[3][0:-1])) * 10000
                else:
                    b[3] = (float(b[3][0:-1])) * 1000
            discc3w += int(b[3])
        print('ghghgggggggghhhhhh',encoutw,discc3w)

        
    #return{'Encout':encoutw,'DisCC3':discc3w}

def get_SwW():
    get_Switch_warning()
    for i in range(len(lstSW)):

        a=get_Switch_warning()
        print('aaaaaaaaaaaaaaaaaaaaa',a)
    #pass
#print('2323232323232ssssss')
#get_SwW()

#######################################
'''def get_Switch_count_list():
    lstSwitchcount = []

    for i in range(len(lstSW)): 
        encout=0
        c = {} 
        for h in range(len(lstSWPorts[i])):
            q=lstSWPorts[i][h]
            b = _SW(lstSW[i],lstSWPorts[i])._dicPartPortError[q]
            #print('dasdssdfsdfsdf',b[2][:-1])
            if b[2][-1] == 'm' or b[2][-1] == 'k':
                if b[2][-1] == 'm':
                    b[2] =(float( b[2][0:-1] ))*10000
                else:
                    b[2] =(float( b[2][0:-1] ))*1000
                #print ('dfdsfdgfdghhhhhhhh',b[2])
            encout += int(b[2])
            c[str(lstSW[i])] = encout
            print("dddddadsdasdsad",c)
            #print("212313213312:",b[2])
        c['IPnow']=lstSW[i]
        lstSwitchcount[int(i)]=(c)
    print ("###222222222222222########:", lstSwitchcount)

    return lstSwitchcount'''


class collHAAP(Document):
    time = DateTimeField(default=datetime.datetime.now())
    engine_status = ListField()


class collSWITCH(Document):
    time = DateTimeField(default=datetime.datetime.now())
    Switch_status = DictField()


#引用参数连接数据库+++++++++++++++++++++++++++++++++++++++++++++
# 方法
class DB_collHAAP(object):
    connect(strDBName, host=strDBServer, port=intDBPort)

    def haap_insert(self, time_now, lstSTS):
        t = collHAAP(time=time_now, engine_status=lstSTS)
        t.save()
    
    def Switch_insert(self, time_now, lstSWS):
        t = collSWITCH(time=time_now, Switch_status=lstSWS)
        t.save()

    def haap_query(self, time_start, time_end):
        collHAAP.objects(date__gte=time_start,
                         date__lt=time_end).order_by('-date')

##By Wen###                         
    def haap_query(self, time_start, time_end):
        collSWITCH.objects(date__gte=time_start,
                         date__lt=time_end).order_by('-date')

    def haap_list_all(self):
        for i in collHAAP.objects().order_by('-time'):
            print(i.time, i.engine_status)

###By Wen####
    def haap_list_all(self):
        for i in collSWITCH.objects().order_by('-time'):
            print(i.time, i.Switch_status)

    def get_N_record_in_list(self, intN):
        N_record = collHAAP.objects().order_by('-time').limit(intN)
        lstRecord = []
        for x in range(len(N_record)):
            lstRecord.append([])
            lstRecord[x].append(N_record[x].time)
            for i in range(len(N_record[x].engine_status)):
                for k in N_record[x].engine_status[i].keys():
                    lstRecord[x].append(N_record[x].engine_status[i][k])
        return lstRecord

#####By Wen########
    def get_N_record_in_list_SW(self, intN):
        N_record = collSWITCH.objects().order_by('-time').limit(intN)
        lstRecord = []
        for x in range(len(N_record)):
            lstRecord.append([])
            lstRecord[x].append(N_record[x].time)
            for i in range(len(N_record[x].Switch_status)):
                for k in N_record[x].Switch_status[i].keys():
                    lstRecord[x].append(N_record[x].Switch_status[i][k])
        return lstRecord
    
    def show_N_record(self, intN):
        r = self.get_N_record_in_list(intN)
        tuplDesc = ('Engine', 'Uptime', 'AH', 'FirmWare',
                   'Status', 'Master', 'Mirror')
        tuplWidth = (18, 16, 7, 13, 9, 9, 12)
        for i in r:
            print('\n Time: %s\n' % str(i[0]))
            w = i[1:]
            for d in range(len(tuplDesc)):
                print(tuplDesc[d].ljust(tuplWidth[d]), end='')
            print()
            for p in w:
                for x in range(len(p)):
                    print(p[x].ljust(tuplWidth[x]), end='')
                print()

 ###By Wen###               
    def show_N_record_Sw(self, intN):
        r = self.get_N_record_in_list_SW(intN)
        tuplDesc = ('FramTX', 'FramRX', 'encout',
                       'Discc3', 'LinkFL', 'LossSC', 'LossSG')
        tuplWidth = (18, 16, 7, 13, 9, 9, 12)
        for i in r:
            print('\n Time: %s\n' % str(i[0]))
            w = i[1:]
            for d in range(len(tuplDesc)):
                print(tuplDesc[d].ljust(tuplWidth[d]), end='')
            print()
            for p in w:
                for x in range(len(p)):
                    print(p[x].ljust(tuplWidth[x]), end='')
                print()

    def get_last_record(self):
        last_record = collHAAP.objects().order_by('-time').first()
        return(last_record.time, last_record.engine_status)
    
#######By Wen#######
    def get_last_record_Switch(self):
        last_record = collSWITCH.objects().order_by('-time').first()
        return(last_record.time, last_record.Switch_status)


# +++++++++从数据库里面拿engine的信息++++++++++++++++
def get_engine_from_db():
    # refresh_time = ['']
    db = DB_collHAAP()
    # def get_last_status():
    last_update = db.get_last_record()
    # print('Last record @ %s' % last_update[0])
    refresh_time = last_update[0]
    lstStatusDict = last_update[1]
    lstStatus = []
    for i in range(len(lstHAAPAlias)):
        #print(lstStatusDict[i][lstHAAPAlias[i]])
        lstStatus.append(lstStatusDict[i][lstHAAPAlias[i]])
        #print(lstStatus)
    return refresh_time, lstStatus


#+++++++++++++++从Switch里面拿数据+++++++++++++++++++++++++
def get_Switch_from_db():
    # refresh_time = ['']
    db = DB_collHAAP()
    # def get_last_status():
    last_update = db.get_last_record_Switch()
    # print('Last record @ %s' % last_update[0])
    refresh_time = last_update[0]
    lstStatusDict = last_update[1]
    lstStatus = []
    lstportcount = []
    lstIPTEST = []
    #print("swwwww:",lstStatusDict)
    
    for i in lstStatusDict:
        if i == "ENCOUT":
            lstencout = lstStatusDict[i][:]
            #print("xxxx:",lstencout)
        elif i =="DISCC3":
            lstdiscc3 = lstStatusDict[i][:]
        else:
            lstStatus.append(lstStatusDict[i])
    #print("sssss:",lstStatus)

    status = []
    for i in lstStatus:
        i = {i['IP'] : i}
       # print (i)
        for j in i:
            i[j].pop('IP')
            #print (i[j])
        print (i)
        print (" ")

        status.append(i)
    #print('zzz',status)
    print("sssssss:",lstStatus)
    return refresh_time, status



###########开始启动wangye###############
def start_web(mode):
    app = Flask(__name__, template_folder='./web/templates',
                static_folder='./web/static', static_url_path='')

    @app.route("/")
    def home():
        lstDesc = ('Engine', 'Uptime', 'AlertHold', 'FirmWare',
                   'Status', 'Master', 'Mirror')
        
        lstDesc_switch = ['PortID', 'FramTX', 'FramRX', 'encout',
                       'Discc3', 'LinkFL', 'LossSC', 'LossSG']
        
        if mode == 'rt':
            refresh_time = _get_TimeNow_Human()
            Status = []
            dictEngines = get_HAAP_status_list()
            for i in range(len(lstHAAPAlias)):
                Status.append(dictEngines[i][lstHAAPAlias[i]])
            # print(Status)

 
################### #    db数据库# # ############################            
        elif mode == 'db':
            tuplHAAP = get_engine_from_db()
            tuplSWITCH = get_Switch_from_db()
            # print(tuplHAAP)
            
            if tuplHAAP:
                refresh_time = tuplHAAP[0]
                Status = tuplHAAP[1]
            else:
                refresh_time = _get_TimeNow_Human()
                Status = None
                
            if tuplSWITCH:
                refresh_time = tuplSWITCH[0]
                Status_Switch = tuplSWITCH[1]
            
            else:
                refresh_time = _get_TimeNow_Human()
                Status_Switch = None

        return render_template("monitor.html",
                               Title=lstDesc,Title_switch=lstDesc_switch,
                               refresh_time=refresh_time,
                               Status=Status, Status_Switch=Status_Switch)

    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)



# 更新传入数据
def job_update_interval(intInterval):
    t = s.Timing()
    db = DB_collHAAP()

    def do_it():
        n = datetime.datetime.now()
        do_update = db.haap_insert(n, get_HAAP_status_list())
        do_update_Switch = db.Switch_insert(n, get_Switch_status_list())
        return do_update, do_update_Switch

    t.add_interval(do_it, intInterval)
    t.stt()
     
 # 更新交换机数据
'''def job_update_interval_Switch(intInterval_Switch):
    t = s.Timing()
    db = DB_collHAAP()

    def do_it_Switch():
        n = datetime.datetime.now()

        
         # print('update complately...@ %s' % n)
        return do_update_Switch
  
    t.add_interval(do_it_Switch, intInterval_Switch)
    t.stt() '''

# def DB_Update_interval(intSec):
#     t = s.Timing()
#     db = DB_collHAAP()
#     def job_update_interval():
#         do_update = db.haap_insert(get_HAAP_status_list())
#         print('update complately...@ %s' % datetime.datetime.now())
#         return do_update

#     t.add_interval(job_update_interval, intSec)
#     t.stt()


# 网页停止
def stopping_web(intSec):
    try:
        print('\nStopping Web Server ', end='')
        for i in range(intSec):
            time.sleep(1)
            print('.', end='')
        time.sleep(1)
        print('\n\nWeb Server Stopped.')
    except KeyboardInterrupt:
        print('\n\nWeb Server Stopped.')


# 启动网页，更新传入数据
def thrd_web_db():
    t1 = Thread(target=start_web, args=('db',))
    t2 = Thread(target=job_update_interval, args=(10,))
    
    t1.setDaemon(True)
    t2.setDaemon(True)

    t1.start()
    t2.start()

    try:
       
        while t2.isAlive():
            pass
        while t1.isAlive():
            pass
    except KeyboardInterrupt:
        stopping_web(3)


def thrd_web_rt():
    t1 = Thread(target=start_web, args=('rt',))
    t1.setDaemon(True)
    t1.start()
    try:
        while t1.isAlive():
            pass
    except KeyboardInterrupt:
        stopping_web(3)

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
            strBackupFolder = '{}/{}'.format(strCFGFolder, _get_TimeNow_Folder())
            for i in lstHAAP:
                _get_HAAPInstance()[i].backup(strBackupFolder)

    # get engines' trace files under TraceFolder based on Trace levels
    elif sys.argv[1] == 'gt':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('gt'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strTraceFolder = '{}/{}'.format(strTCFolder, _get_TimeNow_Folder())
            # for i in lstHAAP:
            #     _get_HAAPInstance()[i].get_trace(strTraceFolder, intTLevel)
            for i in range(len(lstHAAP)):
                _HAAP(lstHAAP[i]).get_trace(strTraceFolder, intTLevel)
            print('\nAll Trace Store in the Folder "%s"' % strTraceFolder)

    elif sys.argv[1] == 'anls':
        if len(sys.argv) != 2:
            print(strHelpSingleCommand.format('anls'))
        elif not _checkIPlst(lstHAAP):
            print('IP error. Please check Engine IPs defined in Conf.ini')
        else:
            strTraceFolder = '{}/{}'.format(strTCAFolder, _get_TimeNow_Folder())
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
                _HAAP(i).set_time()

    elif sys.argv[1] == 'stm':
        for i in lstHAAP:
            _HAAP(i).show_engine_time()

    elif sys.argv[1] == 'wrt':
        thrd_web_rt()
# 第一步
    elif sys.argv[1] == 'wdb':
        thrd_web_db()

    elif sys.argv[1] == 'test':

        # timing_clct_to_db(15)
        # show_N_record(3)
        pass

    else:
        print(strHelp)


if __name__ == '__main__':
    #get_engine_from_db(),get_Switch_from_db()
    #get_SwW()
    get_Switch_from_db()
  #  #get_Switch_status_list()
    main()
    # print("123123:",(_SW('172.16.254.75',[1,2,3])._dicPartPortError[1]))
    # print (type(_SW('172.16.254.75',[1,2,3])._dicPartPortError))
    # print("123123:",(_SW('172.16.254.75',[1,2,3])._dicPartPortError[2]))
    # print("123123:",(_SW('172.16.254.75',[1,2,3])._dicPartPortError[3]))
    # main()
    # SANSW('172.16.254.75', 22, 'admin', 'passwod', [1,2,3])
    # job_update_interval(5)