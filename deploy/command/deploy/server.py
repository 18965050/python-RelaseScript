from time import sleep
from threading import Thread
import os
import re
import sys

from .common import ServerExecutable, executeCmdAndReturn, record
from .common import sourcePath, configPath, jettyPath
from .common import logger


class RedisExecutable(ServerExecutable):
	def __init__(self, option):
		super().__init__(option)
		self.__regRedis = r'redis-server'

	def prequisite(self):
		"""Redis服务操作的必要条件检查"""

		returnCode, out, errMsg = executeCmdAndReturn(['redis-server', '-v'], errMsg='请检查redis是否安装')
		if returnCode != 0:
			self.resCode = returnCode
			self.errMsgs.append(errMsg)

	def isStarted(self):
		returnCode, out, _ = executeCmdAndReturn(['ps -ef|grep redis'], errMsg='redis未启动成功',
		                                         shell=True)
		return True if returnCode == 0 and re.search(self.__regRedis, out) else False

	def start(self):
		demoThread = Thread(target=executeCmdAndReturn,
		                    args=(['redis-server &']),
		                    kwargs={'shell': True, 'log': True})
		demoThread.setDaemon(True)
		demoThread.setName('redis启动线程')
		demoThread.start()
		count = 0
		while not count:
			record('.', terminator='')
			sleep(1)
			if self.isStarted():
				count = 1

			if count > 0:
				break

	def stop(self):
		executeCmdAndReturn(['redis-cli shutdown'], shell=True, log=True)
		while True:
			record('.', terminator='')
			sleep(1)
			if not self.isStarted():
				break


class NginxExecutable(ServerExecutable):
	def __init__(self, option):
		super().__init__(option)
		self.__confFile = 'nginx-io.conf'

	def prequisite(self):
		"""Nginx服务操作的必要条件检查"""

		returnCode, out, errMsg = executeCmdAndReturn(['nginx', '-v'], errMsg='请检查nginx是否安装')
		if returnCode != 0:
			self.resCode = -1
			self.errMsgs.append(errMsg)
			return

		returnCode, out, errMsg = executeCmdAndReturn(['nginx', '-t', '-c', os.path.join(configPath, self.__confFile)],
		                                              cwd=configPath,
		                                              errMsg='nginx配置文件验证不通过')
		if returnCode != 0:
			self.resCode = -1
			self.errMsgs.append(errMsg)

	def isStarted(self):
		returnCode, out, _ = executeCmdAndReturn(['ps -ef|grep nginx'], errMsg='nginx未启动成功',
		                                         shell=True)
		return True if returnCode == 0 and re.search(self.__confFile, out) else False

	def start(self):
		executeCmdAndReturn(['nginx', '-c', os.path.join(configPath, self.__confFile)], cwd=configPath, log=True)
		count = 0
		while not count:
			record('.', terminator='')
			sleep(1)
			if self.isStarted():
				count = 1

			if count > 0:
				break

	def stop(self):
		executeCmdAndReturn(['nginx', '-s', 'stop', '-c', os.path.join(configPath, self.__confFile)], cwd=configPath,
		                    log=True)
		while True:
			record('.', terminator='')
			sleep(1)
			if not self.isStarted():
				break


class IoAllExecutable(ServerExecutable):
	def __init__(self, option):
		super().__init__(option)
		self.pid = None
		self.__regRedis = r'redis-server'
		self.__deployDir = 'io-all/product/io-product-basic/target'
		self.__targetJar = 'io-product-basic.jar'
		returnCode, out, _ = executeCmdAndReturn(['sed \'/dubbo.protocol.port/!d;s/.*=//\' ' + os.path.join(sourcePath,
		                                                                                                    self.__deployDir,
		                                                                                                    'classes/dubbo.properties') + ' | tr -d \'\r\''],
		                                         shell=True)
		self.__serverPort = out[0:len(out) - 1]
		returnCode, out, _ = executeCmdAndReturn(['sed \'/dubbo.protocol.name/!d;s/.*=//\' ' + os.path.join(sourcePath,
		                                                                                                    self.__deployDir,
		                                                                                                    'classes/dubbo.properties') + ' | tr -d \'\r\''],
		                                         shell=True)
		self.__serverProtocol = out[0:len(out) - 1]

	def prequisite(self):
		"""io-all应用操作的必要条件检查"""

		returnCode, out, _ = executeCmdAndReturn(['ps -ef|grep redis'], shell=True)
		if returnCode != 0 or not re.search(self.__regRedis, out):
			self.resCode = returnCode
			self.errMsgs.append('请检查redis是否启动')

	def isStarted(self):
		# 先判断进程是否存在
		returnCode, out, _ = executeCmdAndReturn(['jps -l'], shell=True)
		if returnCode == 0:
			for process in out.split('\n'):
				if re.search(self.__targetJar, process):
					pid = process.split(' ')[0]
					# 再判断端口是否在监听
					returnCode, out, _ = executeCmdAndReturn(['netstat -anp|grep ' + self.__serverPort], shell=True)
					if returnCode == 0:
						for network in out.split('\n'):
							if re.search(pid, network):
								self.pid = pid
								return True

		return False

	def start(self):
		if not self.pid:
			classPath = os.path.join(sourcePath, self.__deployDir, 'lib/*')
			# 如下的命令不会返回结果, 需要通过线程执行
			demoThread = Thread(target=executeCmdAndReturn,
			                    args=(['nohup java -jar ' + self.__targetJar + ' -classpath ' + classPath + ' &']),
			                    kwargs={'cwd': os.path.join(sourcePath, self.__deployDir), 'shell': True, 'log': True})
			demoThread.setDaemon(True)
			demoThread.setName('io-all启动线程')
			demoThread.start()
			count = 0
			while not count:
				record('.', terminator='')
				sleep(1)
				if self.__serverPort and self.__serverProtocol == 'dubbo':
					returnCode, out, _ = executeCmdAndReturn(
						['echo status | nc -i 1 127.0.0.1 ' + self.__serverPort + ' | grep -c OK'],
						shell=True)
					if returnCode == 0:
						count = int(out)
				else:
					if self.isStarted():
						count = 1

				if count > 0:
					break

	def stop(self):
		if self.pid:
			executeCmdAndReturn(['kill ' + self.pid], shell=True, log=True)
			while True:
				record('.', terminator='')
				sleep(1)
				if not self.isStarted():
					break

			self.pid = None


class CkPuckExecutable(ServerExecutable):
	def __init__(self, option):
		super().__init__(option)
		self.dependDict.update({'io-all': IoAllExecutable(None)})
		self.pid = None
		self.__jettyJar = 'start.jar'
		self.__javaOpts = ' -Dspring.profiles.active=development -Ddubbo.resolve.file=webapps/dubbo-resolve.properties '
		self.__serverPort = '8080'

	def prequisite(self):
		"""ck-puck应用操作的必要条件检查"""

		for key in self.dependDict.keys():
			dependApp = self.dependDict.get(key)
			dependApp.prequisite()
			if dependApp.resCode != 0:
				self.resCode = -1
				self.errMsgs.append(dependApp.errMsgs)
				return
			elif not dependApp.isStarted():
				self.resCode = -1
				self.errMsgs.append('请检查 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' 应用是否启动成功')
				return
		if not os.path.exists(os.path.join(jettyPath, 'webapps', 'ck-puck.war')):
			self.resCode = -1
			self.errMsgs.append('ck-puck.war没有部署到jetty容器中')

	def isStarted(self):
		# 先判断进程是否存在
		returnCode, out, _ = executeCmdAndReturn(['jps -l'], shell=True)
		if returnCode == 0:
			for process in out.split('\n'):
				if re.search(self.__jettyJar, process):
					pid = process.split(' ')[0]
					# 再判断端口是否在监听
					returnCode, out, _ = executeCmdAndReturn(['netstat -anp|grep ' + self.__serverPort], shell=True)
					if returnCode == 0:
						for network in out.split('\n'):
							if re.search(pid, network):
								self.pid = pid
								return True

		return False

	def start(self):
		if not self.pid:
			# 如下的命令不会返回结果, 需要通过线程执行
			demoThread = Thread(target=executeCmdAndReturn,
			                    args=([' java -jar ' + self.__jettyJar + self.__javaOpts + ' &']),
			                    kwargs={'cwd': jettyPath, 'shell': True, 'log': True})
			demoThread.setDaemon(True)
			demoThread.setName('ck-puck启动线程')
			demoThread.start()
			count = 0
			while not count:
				record('.', terminator='')
				sleep(1)
				if self.isStarted():
					count = 1

				if count > 0:
					break

	def stop(self):
		if self.pid:
			executeCmdAndReturn(['kill ' + self.pid], shell=True, log=True)
			while True:
				record('.', terminator='')
				sleep(1)
				if not self.isStarted():
					break

			self.pid = None
