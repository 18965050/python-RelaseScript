from abc import ABCMeta, abstractmethod
import subprocess
from functools import wraps
import logging
import logging.config
import os

sourcePath = '/home/INS/source'
commandPath='/home/INS/command'
configPath = '/home/INS/config'
jettyPath = '/opt/jetty-puck'

__logConf = os.path.join(commandPath,'deploy/log.conf')
logging.config.fileConfig(__logConf)
logger = logging.getLogger('release')


class Executable(metaclass=ABCMeta):
	"""
	抽象执行类
	"""

	def __init__(self):
		"""
		初始化构造函数
		resCode: 返回码. 0表示成功, 非0为失败
		errMsgs: 错误消息集合
		"""
		self.resCode = 0
		self.errMsgs = []
		self.dependDict = {}

	@abstractmethod
	def prequisite(self):
		"""
		任务执行的先决条件
		return: True--先决条件满足; False--先决条件不满足"""

		pass

	def execute(self):
		record('开始进行' + self.prequisite.__doc__ + '...')
		self.prequisite()
		if self.resCode != 0:
			for errMsg in self.errMsgs:
				logger.error(errMsg)
			return
		else:
			self.internalExecute()

	@abstractmethod
	def internalExecute(self):
		"""
		具体干活的方法
		:return:
		"""
		record('开始进行' + self.internalExecute.__doc__ + '...')


class ServerExecutable(Executable, metaclass=ABCMeta):
	"""
	Server抽象执行类. 专注于执行 start/stop/restart
	"""

	__options = ['start', 'stop', 'restart']

	def __init__(self, option):
		super().__init__()
		self.option = option.strip() if isinstance(option, str) else None
		self.actionMatched = False

	def _getAppNameFromClsName(self, clsName):
		finalName = ''
		for index, char in enumerate(clsName[:-10]):  # 去除最后的Executable
			if char.isupper():
				if index == 0:
					finalName += char.lower()
				else:
					finalName += ('-' + char.lower())
			else:
				finalName += char

		return finalName

	def internalExecute(self):
		if self.option in ServerExecutable.__options:
			self.actionMatched = True
			if self.option == 'start':
				if self.isStarted():
					record('服务已经在运行了,不需要再启动')
				else:
					record('准备启动 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' ...')
					self.start()
					record(self._getAppNameFromClsName(self.__class__.__name__) + ' 启动成功')
			elif self.option == 'stop':
				if not self.isStarted():
					record('服务已经停止了,不需要再停止')
				else:
					record('准备停止 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' ...')
					self.stop()
					record(self._getAppNameFromClsName(self.__class__.__name__) + ' 停止成功')
			else:
				if self.isStarted():
					record('准备重启 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' ...')
					self.restart()
					record(self._getAppNameFromClsName(self.__class__.__name__) + ' 重启成功')
				else:
					record('准备启动 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' ...')
					self.start()
					record(self._getAppNameFromClsName(self.__class__.__name__) + ' 启动成功')

		if not self.actionMatched:
			record('执行标志不正确, 请检查',level='error')

	@abstractmethod
	def start(self):
		"""
		启动
		:return:
		"""

		pass

	@abstractmethod
	def stop(self):
		"""
		停止
		:return:
		"""
		pass

	@abstractmethod
	def isStarted(self):
		"""
		判断是否启动
		:return: True or False
		"""
		pass

	def restart(self):
		"""
		重启
		:return:
		"""
		record('准备停止 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' ...')
		self.stop()
		record(self._getAppNameFromClsName(self.__class__.__name__) + ' 停止成功')
		record('准备启动 ' + self._getAppNameFromClsName(self.__class__.__name__) + ' ...')
		self.start()
		record(self._getAppNameFromClsName(self.__class__.__name__) + ' 启动成功')


def record(msg,terminator=None, formatter=None, level=None):
	oriTerminatorDict={}
	oriFormatterDict={}
	if terminator is not None:
		for handler in logger.handlers:
			oriTerminatorDict.update({handler.__class__.__name__:handler.terminator})
			handler.terminator=terminator
	if formatter is not None:
		for handler in logger.handlers:
			oriFormatterDict.update({handler.__class__.__name__:handler.formatter._fmt})
			handler.formatter._fmt=formatter
			handler.formatter._style._fmt=formatter

	if level and level in ['debug','info','warning','error','critical']:
		if level=='debug':
			logger.debug(msg)
		elif level=='info':
			logger.info(msg)
		elif level=='warning':
			logger.warning(msg)
		elif level=='error':
			logger.error(msg)
		else:
			logger.critical(msg)
	else:
		logger.info(msg)

	if terminator is not None:
		for handler in logger.handlers:
			handler.terminator=oriTerminatorDict[handler.__class__.__name__]

	if formatter is not None:
		for handler in logger.handlers:
			handler.formatter._fmt=oriFormatterDict[handler.__class__.__name__]
			handler.formatter._style._fmt=oriFormatterDict[handler.__class__.__name__]



def executeCmdAndReturn(*args, **kwargs):
	"""
	执行命令,并根据执行结果返回

	:param args: 命令及命令参数
	:param errMsg: 执行失败时的报错信息
	:return: (returnCode,errMsg)
	"""
	log = kwargs['log'] if kwargs.get('log') else None
	child = subprocess.Popen(*args,  # 1M
	                         cwd=kwargs['cwd'] if kwargs.get('cwd') else None,
	                         shell=kwargs['shell'] if kwargs.get('shell') else False,
	                         # 当shell为True时,args 命令和参数可写在一起
	                         stdin=kwargs['stdin'] if kwargs.get('stdin') else None,
	                         stdout=subprocess.PIPE,
	                         stderr=subprocess.STDOUT)
	bout, _ = child.communicate()
	out=bout.decode('UTF-8')
	if child.returncode == 0:
		if log:
			record(out)
		return (child.returncode, out, '')
	else:
		errMsg = kwargs['errMsg'] if kwargs.get('errMsg') else out
		if log:
			record(errMsg,level='error')
		return (child.returncode, out, errMsg)
