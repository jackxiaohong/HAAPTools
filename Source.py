# coding:utf-8
import os


def GotoFolder(strFolder):
    def _mkdir():
        if os.path.exists(strFolder):
            return True
        else:
            try:
                os.makedirs(strFolder)
                return True
            except Exception as E:
                print(__name__, E)
                print('Create Folder {} Failed...'.format(strFolder))
                return False
    try:
        if _mkdir():
            os.chdir(strFolder)
            return True
    except Exception as E:
        print(__name__, E)
        print('Change to Folder {} Failed...'.format(strFolder))
        return False


def TraceAnalyse(self, oddHAAPErrorDict, strTraceFolder):
    import re
    import xlwt

    def _read_file(strFileName):
        try:
            with open(strFileName, 'r+') as f:
                strTrace = f.read()
            return strTrace.strip().replace('\ufeff', '')
        except Exception as E:
            print('Open File {} Failed...'.format(strFileName))
            return None

    def _trace_analize(lstTraceFiles):
        intErrFlag = 0
        strRunResult = ''
        for strFileName in lstTraceFiles:
            if (lambda i: i.startswith('Trace_'))(strFileName):
                print('\n{}  Analysing ...'.format(strFileName))
                strRunResult += '\n{}  Analysing ...\n'.format(strFileName)
                openExcel = xlwt.Workbook()
                for strErrType in oddHAAPErrorDict.keys():
                    reErr = re.compile(oddHAAPErrorDict[strErrType])
                    tupErr = reErr.findall(_read_file(strFileName))
                    if len(tupErr) > 0:
                        strOut = " *** {} Times of {} Found...".format(
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
                    else:
                        pass
                    reErr = None
                else:
                    pass
                if intErrFlag > 0:
                    openExcel.save('TraceAnalyse_' +
                                   strFileName + '.xls')
                else:
                    strOut = '--- No Error in {}'.format(strFileName)
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
