import re
import os
import datetime
import getpass
import ClassSW as sw

# lstCommand = 'conmgr status'

# if isinstance(lstCommand, str):
#     lstCommand = lstCommand.split('!@#$%^&*')

# print(lstCommand)

# if None:
# 	print('aa')



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


#####------------Range list

# lstCommand = list('goodman')

# for i in range(len(lstCommand)):
#     print(lstCommand[i])
#     print(i)
#     i += 1
#     print(i)

####--------------File absolute dir
# def mkdir(strResultFolder):
#     strOldDir = os.getcwd()
#     try:
#         os.makedirs(strResultFolder)
#     except OSError as E:
#         pass
#     os.chdir(strResultFolder)
#     os.chdir(strOldDir)


#####-------------import in the function

# def p():
#     import pprint
#     pprint.pprint(list('WTForm'))

# def strTime():
#     strTimeNow = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
#     return 'Trace_' + strTimeNow
    # print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-7])

if __name__ == '__main__':
    # print(strTime())
    sw.SANSW('172.16.254.75', 22, strSWUser, strSWPWD, lstSWPorts[i])
    
