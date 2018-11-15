from __future__ import print_function
from ClassConnect import *
from collections import OrderedDict
import re
import Source as s
import pprint


def deco(func):
    def _deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as E:
            print('Please Check SAN Switch connection...')
            print(func.__name__)
            print(E)
    return _deco


def deco_Exception(func):
    def _deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as E:
            print(self._host, func.__name__, E)
    return _deco


class SANSW(object):
    def __init__(self, strIP, intPort, strUserName, strPasswd,
                 lstSWPort, intTimeout=2):
        self._host = strIP
        self._port = intPort
        self._username = strUserName
        self._password = strPasswd
        self._timeout = intTimeout
        self._allSWPort = lstSWPort
        self._strAllPortError = None
        self._dicPartPortError = None
        self._SANSWConnection = None
        self._getporterrshow()
        self._PutErrorToDict()

    @deco_Exception
    def _getporterrshow(self):
        try:
            self._SANSWConnection = SSHConn(self._host,
                                     self._port,
                                     self._username,
                                     self._password,
                                     self._timeout)
            self._strAllPortError = self._SANSWConnection.ExecuteCommand('porterrshow')
            return True
        except Exception as E:
            s.ShowErr(self.__class__.__name__,
                          sys._getframe().f_code.co_name,
                          'Get PortErrorInfo for "{}" Fail with Error:'.format(
                              self._host),
                          E)

        # except Exception as E:
        #     print('Connect to SAN Switch {} Failed...'.format(self._host))
        #     print(E)

    def _PutErrorToDict(self):
        def _portInLine(intSWPort, strLine):
            lstLine = strLine.split()
            if (str(intSWPort) + ':') in lstLine:
                return True

        def _getErrorAsList(intPortNum, lstPortErrLines):
            for portErrLine in lstPortErrLines:
                if _portInLine(intPortNum, portErrLine):
                    reDataAndErr = re.compile(
                        r'(.*:)((\s+\S+){2})((\s+\S+){6})((\s+\S+){5})(.*)')
                    resultDataAndErr = reDataAndErr.match(portErrLine)
                    return(resultDataAndErr.group(2).split() +
                           resultDataAndErr.group(6).split())

        def _putToDict():
            dicPort_Error = OrderedDict()
            lstPortErrLines = str(self._strAllPortError).split('\n')
            for intPortNum in self._allSWPort:
                lstErrInfo = _getErrorAsList(intPortNum, lstPortErrLines)
                dicPort_Error[intPortNum] = lstErrInfo
            self._dicPartPortError = dicPort_Error

        if self._strAllPortError:
            _putToDict()
        # else:
        #     if self._getporterrshow():
        #         _putToDict()


    def _porterrshow(self):
        if self._strAllPortError:
            print('Porterrshow for SAN Switch {}:\n'.format(self._host))
            print(self._strAllPortError)

    def _switchshow(self):
        if self._SANSWConnection:
            try:
                print('Switchshow for SAN Switch {}:\n'.format(self._host))
                print(self._SANSWConnection.ExecuteCommand('switchshow'))
            except Exception as E:
                pass

    @deco_Exception
    def get_linkfail_by_port(self, intSWPort):
        if self._dicPartPortError:
            if intSWPort in self._dicPartPortError.keys():
                return self._dicPartPortError[intSWPort][4]
            else:
                return 'Please Correct the Port Number...'
        else:
            print('Please initialization SAN Switch connect first...')

    @deco_Exception
    def get_encout_by_port(self, intSWPort):
        if self._dicPartPortError:
            if intSWPort in self._dicPartPortError.keys():
                return self._dicPartPortError[intSWPort][2]
            else:
                print('Please Correct the Port Number...')
        # else:
        #     print('Get Error Dict First...')

    @deco_Exception
    def get_discC3_by_port(self, intSWPort):
        if self._dicPartPortError:
            if intSWPort in self._dicPartPortError.keys():
                return self._dicPartPortError[intSWPort][3]
            else:
                print('Please Correct the Port Number...')
        # else:
        #     print('Get Error Dict First...')

    @deco_Exception
    def get_encout_total(self):
        def _get_count():
            int_encoutTotal = 0
            for i in self._dicPartPortError:
                if 'k' in self._dicPartPortError[i][2]:
                    return 'Over Thousand Errors of encout detected...'
                elif 'm' in self._dicPartPortError[i][2]:
                    return 'Over Million Errors of encout detected...'
                int_encoutTotal += int(self._dicPartPortError[i][2])
            return int_encoutTotal
        if self._dicPartPortError:
            return _get_count()
        # else:
        #     print('Get Error Dict First...')
        #     return None

    @deco_Exception
    def get_discC3_total(self):
        def _get_count():
            int_encoutTotal = 0
            for i in self._dicPartPortError:
                if 'k' in self._dicPartPortError[i][3]:
                    return 'Over Thousand Errors of encout detected...'
                elif 'm' in self._dicPartPortError[i][3]:
                    return 'Over Million Errors of encout detected...'
                int_encoutTotal += int(self._dicPartPortError[i][3])
            return int_encoutTotal
        if self._dicPartPortError:
            return _get_count()
        # else:
        #     print('Get Error Dict First...')
        #     return None

    # @deco_Exception
    def clear_porterr_All(self):
        if self._SANSWConnection:
            try:
                self._SANSWConnection.ExecuteCommand('statsclear')
                print('Clear Error Count for SW "{}" Completely...'.format(self._host))
            except Exception as E:
                pass
        else:
            print('Connect to SAN Switch lost...')

    @deco_Exception
    def clear_porterr_by_port(self, intSWPort):
        if self._boolConnectStatus:
            try:
                self._SANSWConnection.ExecuteCommand(
                    'portstatsclear {}'.format(str(intSWPort)))
                return True
            except Exception as E:
                print('Clear Error Count Failed...')
                return False
        else:
            print('Connect to SAN Switch lost...')
            return False

    @deco_Exception
    def show_porterrors(self):
        def _show_porterrors():
            lstDesc = ['PortID', 'FramTX', 'FramRX', 'encout',
                       'Discc3', 'LinkFL', 'LossSC', 'LossSG']
            for strDesc in lstDesc:
                print(strDesc.center(8), end='')
            print()
            for intPort in self._dicPartPortError:
                print(str(intPort).center(8), end='')
                for strPortErr in self._dicPartPortError[intPort]:
                    print(strPortErr.center(8), end='')
                print()
        if self._dicPartPortError:
            print('\nThe Ports Errors of SAN Switch {} ...'.format(self._host))
            _show_porterrors()
        # else:
        #     print('Get Error Dict First...')
        #     return None


if __name__ == '__main__':
    lstPort = [2, 3, 4, 5]
    sw1 = SANSW('172.16.254.77', 22, 'admin', 'password', lstPort)
    # pprint.pprint(sw1._dicPartPortError)
    # print(sw1.get_encout_total())
    # print(sw1.get_discC3_total())
    # print(sw1.get_discC3_by_port(3))
    # # print(sw1.get_encout_by_port(20))
    # # print(sw1.get_linkfail_by_port(4))
    # # sw1.clear_porterr_by_port(3)
    # # print(sw1.get_encout_by_port(2))
    # sw1._dicPartPortError = None
    # print(sw1.get_discC3_by_port(3))
    print(sw1.show_porterrors())

    # print(sw1.get_encout_by_port(3))
    # lstSW = ['172.16.254.75', '172.16.254.76']

    # lstSWinstance = []
    # oddSWObject = OrderedDict()
    # for i in lstSW:
    #     locals()['SW' + str(i)] = SANSW(i, 22, 'admin', 'password', lstPort)
    #     lstSWinstance.append(locals()['SW' + str(i)])
    #     # print(str('SW' + str(i)))
    #     oddSWObject[str('SW' + str(i))] = locals()['SW' +
    #                                                str(i)]._dicPartPortError

    # pprint.pprint(oddSWObject)

    # print(dir(SANSW))
