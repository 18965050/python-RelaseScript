import re
import os

from .common import Executable, executeCmdAndReturn, record
from .common import sourcePath, jettyPath
from .server import IoAllExecutable, CkPuckExecutable


class CompileExecutable(Executable):
	"""
	编译,打包应用业务执行类
	"""

	def __init__(self, app):
		super().__init__()
		self.apps = ['io-all', 'ck-puck', 'ck-puck-front'] if app.strip() == 'all' else [app.strip()]
		for app in self.apps:
			if app == 'io-all':
				self.dependDict.update({'io-all': IoAllExecutable(None)})
			elif app == 'ck-puck':
				self.dependDict.update({'ck-puck': CkPuckExecutable(None)})

		self.__regJavaVersion = r'java version "[1.8|1.9].*'
		self.__regMavenVersion = r'^Apache Maven 3.*'
		self.__regNodeVersion = r'v[4-8]\..*'
		self.__regNpmVersion = r'[3-6]\..*'
		self.__choiceDict = {'io-all': ['mvn clean install -Dmaven.test.skip=true',  # 命令
		                                'product/io-product-basic/target/io-product-basic.jar'],  # 文件是否存在验证正则
		                     'ck-puck': ['mvn clean package -Dmaven.test.skip=true',
		                                 'target/ck-puck.war'],
		                     'ck-puck-front': ['ln -s /home/INS/source/node_modules/ node_modules; rm -rf dist; npm install; npm run build', 'dist']}

	def prequisite(self):
		"""项目编译的必要条件检查"""

		for app in self.apps:
			if app == 'io-all' or app == 'ck-puck':
				returnCode, out, errMsg = executeCmdAndReturn(['java', '-version'], errMsg='请检查JDK是否安装')
				if returnCode == 0:
					if not re.search(self.__regJavaVersion, out):
						self.resCode = -1
						self.errMsgs.append('jdk版本必须要是1.8以上的版本')
				else:
					self.resCode = -1
					self.errMsgs.append(errMsg)

				returnCode, out, errMsg = executeCmdAndReturn(['mvn', '-version'], errMsg='请检查MAVEN是否安装')
				if returnCode == 0:
					if not re.search(self.__regMavenVersion, out):
						self.resCode = -1
						self.errMsgs.append('MAVEN版本必须要是3.0以上的版本')
				else:
					self.resCode = -1
					self.errMsgs.append(errMsg)

			elif app == 'ck-puck-front':
				returnCode, out, errMsg = executeCmdAndReturn(['node', '-v'], errMsg='请检查Node.js是否安装')
				if returnCode == 0:
					if not re.search(self.__regNodeVersion, out):
						self.resCode = -1
						self.errMsgs.append('Node.js版本必须要是4.0.0以上的版本')
				else:
					self.resCode = -1
					self.errMsgs.append(errMsg)

				returnCode, out, errMsg = executeCmdAndReturn(['npm', '-v'], errMsg='请检查NPM是否安装')
				if returnCode == 0:
					if not re.search(self.__regNpmVersion, out):
						self.resCode = -1
						self.errMsgs.append('NPM版本必须要是3.0.0以上的版本')
				else:
					self.resCode = -1
					self.errMsgs.append(errMsg)

				if not os.path.exists(os.path.join(sourcePath,'node_modules')):
					self.resCode=-1
					self.errMsgs.append('请确认'+os.path.join(sourcePath,'node_modules')+'路径存在')

	def internalExecute(self):
		"""应用编译"""

		super().internalExecute()
		for app in self.apps:
			dependApp = self.dependDict.get(app)
			if dependApp and dependApp.isStarted():
				dependApp.stop()

			returnCode, _, _ = executeCmdAndReturn(self.__choiceDict[app][0], cwd=os.path.join(sourcePath, app),
			                                       shell=True,log=True)
			if returnCode == 0 and os.path.exists(os.path.join(sourcePath, app, self.__choiceDict[app][1])):
				record('编译打包' + app + '项目成功')
			else:
				record('编译打包' + app + '项目失败')

			if app == 'ck-puck-front':
				executeCmdAndReturn(['rm -rf *.json.gzip'],
				                    cwd=os.path.join(sourcePath, app), shell=True)  # 删除编译输出临时文件

			if app == 'ck-puck':
				executeCmdAndReturn(['cp -f ' + self.__choiceDict[app][1] + ' ' + os.path.join(jettyPath, 'webapps')],
				                    cwd=os.path.join(sourcePath, app), shell=True)  # 拷贝目标war包到jetty容器中
				executeCmdAndReturn(['cp -f ' + os.path.join(sourcePath, app,
				                                             'src/test/resources/properties/dubbo-resolve.properties') + ' ' + os.path.join(
					jettyPath, 'webapps')],
				                    cwd=os.path.join(sourcePath, app),
				                    shell=True)  # 拷贝dubbo-resolve.properties到指定路径下, 确保只会引用本地的服务
