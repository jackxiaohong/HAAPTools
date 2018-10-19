# coding:utf-8
import ClassSW as sw
import ClassHAAP as haap
import Source as s
from collections import OrderedDict as Odd
import configparser as cp
import os
import sys
import datetime
import getpass
import pprint

#----------------------------------------- 动态对象实例化及访问
# lstSW = ['172.16.254.75', '172.16.254.76']
# lstSWPorts = [[2, 3, 4, 5], [2, 3, 4, 5]]
# # 用字典键作为实例化对象名，字典值即是相对应的对象
# oddSWObject = Odd()
# for i in range(len(lstSW)):
#     oddSWObject['SW' + str(lstSW[i])] = sw.SANSW(lstSW[i],
#                                                  22, 'admin',
#                                                  'password',
#                                                  lstPort[i])
# print(oddSWObject)
# for i in oddSWObject.values():
#     print(i.get_discC3_by_port(3))

# for i in oddSWObject.keys():
#     print(oddSWObject[i].get_discC3_by_port(3))

# ip = '172.16.254.75'
# print('...')
# print(oddSWObject['SW' + ip].get_discC3_by_port(3))

# # 动态定义变量名作为实例化对象名，调用时需要手动写变量名或者用locals动态调用
# print('###')
# for i in range(len(lstSW)):
#     locals()['SW' + str(i)] = sw.SANSW(lstSW[i],
#                                        22, 'admin', 'password', lstPort[i])
# print(SW0.get_discC3_by_port(3))
# print(locals()['SW0'].get_discC3_by_port(3))
# 直接用SAN交换机IP地址（字典键值）做实例名，动态生成实例字典
# oddSWInst = OrderedDict()
#     for i in range(len(lstSW)):
#         oddSWInst[lstSW[i]] = SANSW(lstSW[i], 22, 'admin', 'password', lstPort[i])
#     print(oddSWInst)
#     for i in lstSW:
#         print(oddSWInst[i].get_discC3_by_port(3))


strHelp = '''
        -run            : Run Normally
        -porterrshow    : Run, but Collect PortError only
        -statsclear     : Clear PortError Counter on the SAN Switch
        -zipall         : Zip All non-Zip File
        -check          : Run Periodic Check
        '''


strTimeNow = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


objCFG = cp.ConfigParser(allow_no_value=True)
objCFG.read('Conf.ini')

# <<<SAN Switch Config>>>
strSWUser = objCFG.get('SWSetting', 'username')
strSWPWD = objCFG.get('SWSetting', 'password')
intSWSSHPort = objCFG.get('SWSetting', 'port')

oddSWPort = Odd()
for i in objCFG.items('SWPorts'):
    oddSWPort[i[0]] = eval(i[1])

lstSW = list(oddSWPort.keys())
lstSWPorts = list(oddSWPort.values())

strSWPortErrorFolder = objCFG.get('FolderSetting', 'porterrfolder')

# <<<HAAP Config>>>
lstEngineIPs = list(i[0] for i in objCFG.items('Engines'))
intTraceLevel = int(objCFG.get('TraceSetting', 'TraceLevel'))
intTelnetPort = int(objCFG.get('EngineSetting', 'TelnetPort'))
intFTPPort = int(objCFG.get('EngineSetting', 'FTPPort'))
lstCheckCommand = list(i[0] for i in objCFG.items('PeriodicCheckCommand'))

strHAAPPasswd = objCFG.get('EngineSetting', 'HAAPPassword')
if strHAAPPasswd:
    strHAAPPasswd = strHAAPPasswd
else:
    strHAAPPasswd = getpass.getpass(
        prompt='Please Input Your Engine Password: ', stream=None)


def main():

    if len(sys.argv) == 1 or len(sys.argv) > 2:
        print(strHelp)

    # elif sys.argv[1] == '-run':
    #     moduleOldFileClean.Clean()
    #     moduleGetTrace.GetTrace()
    #     moduleTraceAnalyse.TraceAnalyze()
    #     moduleSWPortErrorAnalyze.SWPortErrorAnalyze()
    #     moduleZipCollections.ZipCollections()

    elif sys.argv[1] == '-porterrshow':
        oddSWInst = Odd()
        for i in range(len(lstSW)):
            oddSWInst[lstSW[i]] = sw.SANSW(lstSW[i], intSWSSHPort,
                                           strSWUser, strSWPWD, lstSWPorts[i])
        print(oddSWInst)
        for i in lstSW:
            oddSWInst[i].show_porterrors()

    # elif sys.argv[1] == '-statsclear':
    #     moduleClearPortError.ClearPortError()

    # elif sys.argv[1] == '-zipall':
    #     moduleZipCollections.ZipAll()

    # elif sys.argv[1] == '-check':
    #     modulePeriodicCheck.main()

    else:
        print(strHelp)


if __name__ == '__main__':
    main()
