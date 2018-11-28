# coding:utf-8
import os
import sys
import time
from mongoengine import *
from apscheduler.schedulers.blocking import BlockingScheduler
import re
import xlwt

# read from conf.ini level = 1
error_level = 1

# def ShowErr_level3(_class, _func, _Msg, _Error=''):
#     pass

def ShowErr(*argvs):
    if len(argvs) == 3:
        argvs[3] = ''

    if error_level == 1:
        print(str('''
----------------------------------------------------------------------------
|*Error Message:                                                           |
|    Error Message: {:<55}|
|        {:<66}|
----------------------------------------------------------------------------\
'''.format(argvs[2], argvs[3])))
    elif error_level == 2:
        return ShowErr_level2(argvs)
    elif error_level == 3:
        print(str('''
----------------------------------------------------------------------------
|*Error Message:                                                           |
|    Class Name :   {:<55}|
|    Function name: {:<55}|
|    Error Message: {:<55}|
|        {:<66}|
----------------------------------------------------------------------------\
'''.format(argvs[0], argvs[1], argvs[2], argvs[3])))

def GotoFolder(strFolder):
    def _mkdir():
        if os.path.exists(strFolder):
            return True
        else:
            try:
                os.makedirs(strFolder)
                return True
            except Exception as E:
                print('Create Folder "{}" Fail With Error:\n\t"{}"'.format(
                    strFolder, E))

    if _mkdir():
        try:
            os.chdir(strFolder)
            return True
        except Exception as E:
            print('Change to Folder "{}" Fail With Error:\n\t"{}"'.format(
                strFolder, E))


class Timing(object):
    def __init__(self):
        self.scdl = BlockingScheduler()

    def add_interval(self, job, intSec):
        self.scdl.add_job(job, 'interval', seconds=intSec, max_instances=6)

    def add_once(self, job, rdate):
        try:
            self.scdl.add_job(job, 'date', run_date=rdate, max_instances=6)
        except ValueError as E:
            self.scdl.add_job(job, 'date')
        
    def stt(self):
        self.scdl.start()

    def stp(self):
        self.scdl.shutdown()

def ttt():
    t = Timing()
    
    def job_update_interval():
        print('update complately...')
    
    t.add_interval(job_update_interval, 2)
    t.stt()


class TimeNow(object):
    def __init__(self):
        self._now = time.localtime()

    def y(self):    # Year
        return (self._now[0])

    def mo(self):   # Month
        return (self._now[1])

    def d(self):    # Day
        return (self._now[2])

    def h(self):    # Hour
        return (self._now[3])

    def mi(self):   # Minute
        return (self._now[4])

    def s(self):    # Second
        return (self._now[5])

    def wd(self):  # Day of the Week
        return (self._now[6])



# class store_in_MongoDB():
#     def __init__(self, ):
#         self.DBServer = strDBServer
#         self.DBPort = intDBPort
#         self.DBName = strDBName
#         connect()
#         self._DB = None
#         self._connect()

#     def _connect(self):
#         dbConn = MongoClient(self.DBServer, self.DBPort)
#         # db = dbConn.'%s' % self.strDBName
#         dbName = self.DBName
#         self._DB = dbConn.dbName

#     def coll_insert(self, coll_name, value):
#         if self._DB:
#             locals()[coll_name] = self._DB.coll_name
#             locals()[coll_name].insert(value)


def TraceAnalyse(oddHAAPErrorDict, strTraceFolder):

    def _read_file(strFileName):
        try:
            with open(strFileName, 'r+') as f:
                strTrace = f.read()
            return strTrace.strip().replace('\ufeff', '')
        except Exception as E:
            print('Open File "{}" Failed With Error:\n\t"{}"'.format(
                strFileName, E))

    def _trace_analize(lstTraceFiles):
        intErrFlag = 0
        strRunResult = ''
        for strFileName in lstTraceFiles:
            if (lambda i: i.startswith('Trace_'))(strFileName):
                print('\n"{}"  Analysing ...'.format(strFileName))
                strRunResult += '\n"{}"  Analysing ...\n'.format(strFileName)
                openExcel = xlwt.Workbook()
                for strErrType in oddHAAPErrorDict.keys():
                    reErr = re.compile(oddHAAPErrorDict[strErrType])
                    tupErr = reErr.findall(_read_file(strFileName))
                    if len(tupErr) > 0:
                        strOut = ' *** "{}" Times of "{}" Found...'.format(
                            (len(tupErr) + 1), strErrType)
                        print(strOut)
                        strRunResult += strOut
                        objSheet = openExcel.add_sheet(strErrType)
                        for x in range(len(tupErr)):
                            for y in range(len(tupErr[x])):
                                objSheet.write(
                                    x, y, tupErr[x][y].strip().replace(
                                        "\n", '', 1))
                        intErrFlag += 1
                    reErr = None
                if intErrFlag > 0:
                    openExcel.save('TraceAnalyse_' +
                                   strFileName + '.xls')
                else:
                    strOut = '--- No Error Find in "{}"'.format(strFileName)
                    print(strOut)
                    strRunResult += strOut
                intErrFlag = 0
        return strRunResult

    strOriginalFolder = os.getcwd()
    try:
        GotoFolder(strTraceFolder)
        lstTraceFile = os.listdir('.')
        _trace_analize(lstTraceFile)
    finally:
        os.chdir(strOriginalFolder)


if __name__ == '__main__':
    # a = store_in_MongoDB('HDB')
    # cn = {'2':'3'}
    # a.coll_insert('aa', cn)

    #ttt()
    print('www')


