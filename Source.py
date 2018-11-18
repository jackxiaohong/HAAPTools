# coding:utf-8
import os
import sys
import time


def ShowErr(_class, _func, _Msg, _Error=''):
    print(str('''
----------------------------------------------------------------------------
|*Error Message:                                                           |
|    Class Name :   {:<55}|
|    Function name: {:<55}|
|    Error Message: {:<55}|
|        {:<66}|
----------------------------------------------------------------------------\
'''.format(_class, _func, _Msg, _Error)))


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


def TraceAnalyse(oddHAAPErrorDict, strTraceFolder):
    import re
    import xlwt

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
