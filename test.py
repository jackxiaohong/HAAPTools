import re
import os
import datetime
import getpass
import ClassSW as sw
import sys
import inspect

# lstCommand = 'conmgr status'

# if isinstance(lstCommand, str):
#     lstCommand = lstCommand.split('!@#$%^&*')

# print(lstCommand)

# if None:
#   print('aa')


# def P(x, y):

#     def pp():
#         print(x)

#     print(y)
#     pp()
# P(2,3)

# vpd = '''IP address         : 177.222.108.1
# Uptime             : 7days 00:04:41
# Alert: None
# Tuesday, 7/14/2015, 11:40:54
# 177.222.108.1'''

# reUpTime = re.compile(r'Uptime.* \: (.*)')
# strUpTime = reUpTime.findall(vpd)

# print(strUpTime)

# reUpTimeList = re.compile(r'(\d*)days (\d{2}):(\d{2}):(\d{2})')

# print(reUpTimeList.match(strUpTime[0]).groups())

# aa = re.compile(r'.*((\d{3}.)(\d{3}.)(\d{3}.))')
# print(aa.match(vpd).groups())


# ------------Range list

# lstCommand = list('goodman')

# for i in range(len(lstCommand)):
#     print(lstCommand[i])
#     print(i)
#     i += 1
#     print(i)

# --------------File absolute dir
# def mkdir(strResultFolder):
#     strOldDir = os.getcwd()
#     try:
#         os.makedirs(strResultFolder)
#     except OSError as E:
#         pass
#     os.chdir(strResultFolder)
#     os.chdir(strOldDir)


# -------------import in the function

# def p():
#     import pprint
#     pprint.pprint(list('WTForm'))

# def strTime():
#     strTimeNow = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
#     return 'Trace_' + strTimeNow
# print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-7])


# get trace name...

# result = '''
# >ftpprep trace

# ftp_data_20181021_114517.txt has been created in the mbtrace directory
# '''
# def gt(result):
#     reTraceName = re.compile(r'(ftp_data_\d{8}_\d{6}.txt)')
#     strTraceName = reTraceName.search(result)
#     if strTraceName:
#         print(strTraceName.group())
#         return strTraceName

# raise...

# def get_current_function_name():
#     return inspect.stack()[1][3]

# def deco_Exception(func):
#     def _deco(self, *args, **kwargs):
#         try:
#             return func(self, *args, **kwargs)
#         except Exception as E:
#             print(self.__class__.__name__,
#                 sys._getframe().f_code.co_name,
#                       func.__name__,
#                       get_current_function_name(),
#                       E)
#     return _deco

# @deco_Exception
# def t(y):
#     def r(x):
#         if x == 1:
#             print(x)
#         else:
#             raise ValueError, "{} Cuo le....".format(get_current_function_name())
#     r(y)

### For ...

def p(x):
    print(x)

if __name__ == '__main__':
    # print(strTime())
    # sw.SANSW('172.16.254.75', 22, strSWUser, strSWPWD, lstSWPorts[i])
    # gt(result)
    # raise_test(1)
    # def x(w):
    #     t(w)

    # x('x')

    # def _ShowErrors(strError,
    #  funcName=sys._getframe().f_code.co_name,
    #  ):
    #     return str('''
    # Errors:
    #     Class Name :   {}
    #     Function name: {}
    #     Error Message: {}
    #         '''.format(self.__class__.__name__,
    #             funcName,
    #             strError))
    # print(_ShowErrors('wps'))


    # def i():
    #     def showFunc(x=sys._getframe().f_code.co_name):
    #         print(x)
    #     showFunc()

    # i()


    a = 'ABCD'
    print('"%s - %s"' % (a, a))
    print('I am a %8s----\
%d' % (a, 8))
    # print(f"{a}")
