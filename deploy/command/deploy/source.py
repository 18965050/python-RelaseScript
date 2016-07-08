import os
import re

from .common import Executable, executeCmdAndReturn,record
from .common import sourcePath
from .server import IoAllExecutable, CkPuckExecutable


class SourceExecutable(Executable):
	"""
	下载源代码业务执行类
	"""

	def __init__(self, app, branch):
		super().__init__()
		self.apps = ['io-all', 'ck-puck', 'ck-puck-front'] if app.strip() == 'all' else [app.strip()]
		for app in self.apps:
			if app == 'io-all':
				self.dependDict.update({'io-all': IoAllExecutable(None)})
			elif app == 'ck-puck':
				self.dependDict.update({'ck-puck': CkPuckExecutable(None)})

		self.branch = branch.strip()
		self.__regStr = r'^git version [0|1].*'
		self.__gitRepoDict = {'ck-puck-front': 'git:ck/ck-puck-front.git',
		                      'ck-puck': 'git:ck/ck-puck.git',
		                      'io-all': 'git:io/io-all.git'}

	def prequisite(self):
		"""获取源码的必要条件检查"""

		returnCode, out, errMsg = executeCmdAndReturn(['git', '--version'], errMsg='请检查git是否安装')
		if returnCode == 0:
			if re.search(self.__regStr, out):
				self.resCode = -1
				self.errMsgs.append('git版本必须要是2.0以上的版本')
		else:
			self.resCode = returnCode
			self.errMsgs.append(errMsg)

	def internalExecute(self):
		"""源码下载"""

		super().internalExecute()
		for app in self.apps:
			dependApp = self.dependDict.get(app)
			if dependApp and dependApp.isStarted():
				dependApp.stop()

			self.__gitOper(sourcePath, app, self.__gitRepoDict[app])

	def __gitOper(self, path, repo, gitUrl):
		gitOk = False
		appPath = os.path.join(path, repo)
		if os.path.exists(appPath):
			gitPath = os.path.join(appPath, '.git')
			if os.path.exists(gitPath):
				returnCode, _, _ = executeCmdAndReturn(['git', 'status'], cwd=appPath)
				if (not returnCode):
					gitOk = True

		if gitOk:
			executeCmdAndReturn(['git', 'reset', '--hard'], cwd=appPath, log=True)
			executeCmdAndReturn(['git', 'clean', '-ffdx'], cwd=appPath, log=True)
			executeCmdAndReturn(['git', 'fetch'], cwd=appPath, log=True)
		else:
			executeCmdAndReturn(['rm -rf ' + repo], cwd=path, shell=True, log=True)
			executeCmdAndReturn(['git clone --no-checkout ' + gitUrl], cwd=path, shell=True, log=True)

		record('检出仓储' + repo + '分支' + self.branch + '的对应代码')
		executeCmdAndReturn(['git', 'checkout', '-f', self.branch], cwd=appPath, log=True)
		executeCmdAndReturn(['git', 'pull'], cwd=appPath, log=True)
		executeCmdAndReturn(['git submodule update --init --recursive --force'], cwd=appPath, shell=True, log=True)
