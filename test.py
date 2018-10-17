import re

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

vpd = '''IP address         : 177.222.108.1
Uptime             : 7days 00:04:41
Alert: None
Tuesday, 7/14/2015, 11:40:54
177.222.108.1'''

reUpTime = re.compile(r'Uptime.* \: (.*)')
strUpTime = reUpTime.findall(vpd)

print(strUpTime)

reUpTimeList = re.compile(r'(\d*)days (\d{2}):(\d{2}):(\d{2})')

print(reUpTimeList.match(strUpTime[0]).groups())

aa = re.compile(r'.*((\d{3}.)(\d{3}.)(\d{3}.))')
print(aa.match(vpd).groups())




