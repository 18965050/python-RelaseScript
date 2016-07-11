#!/home/python35/bin/python
"""
IO项目发布脚本. 选择需要执行的发布命令, 进行不同的发布操作
	source: 获取源文件
	compile: 编译,打包源代码
	redis: 启动/停止/重启 redis
	nginx: 启动/停止/重启 nginx
	io-all: 启动/停止/重启 io-all应用
	ck-puck: 启动/停止/重启 ck-puck应用
	all: 应用源码下载, 编译打包,启动一条龙服务
"""

import argparse
import os

# for remote debug
import pydevd
pydevd.settrace('192.168.27.92', port=10088, stdoutToServer=True, stderrToServer=True)

from deploy import *

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='IO项目发布脚本', formatter_class=argparse.RawTextHelpFormatter)

	parser.add_argument('-x', '--execute', dest='target', metavar='target', required=True, action='store',
	                    choices=('source', 'compile', 'redis', 'nginx', 'io-all', 'ck-puck', 'all'),
	                    default='all',
	                    help='''请选择执行的操作:
-------------------------------------------------------------------------------------------------------------
|   操作   |              操作说明               |         选项         |             选项说明               |
-------------------------------------------------------------------------------------------------------------
|          |                                     |    io-all,branch     |   获取io-all应用branch分支源码     |
|  source  |             下载源代码              |    ck-puck,branch    |   获取ck-puck应用branch分支源码    |
|          |                                     | ck-puck-front,branch | 获取ck-puck-front应用branch分支源码|
|          |                                     |       all,branch     |    获取所有应用branch分支源码      |
-------------------------------------------------------------------------------------------------------------
|          |                                     |        io-all        |        编译打包io-all应用          |
|  compile |           应用编译打包              |       ck-puck        |        编译打包ck-puck应用         |
|          |                                     |     ck-puck-front    |      编译打包ck-puck-front应用     |
|          |                                     |         all          |          编译打包所有应用          |
-------------------------------------------------------------------------------------------------------------
|          |                                     |        start         |            启动redis服务           |
|  redis   |           redis服务操作             |        stop          |            停止redis服务           |
|          |                                     |       restart        |            重启redis服务           |
-------------------------------------------------------------------------------------------------------------
|          |                                     |        start         |            启动nginx服务           |
|  nginx   |           nginx服务操作             |        stop          |            停止nginx服务           |
|          |                                     |       restart        |            重启nginx服务           |
-------------------------------------------------------------------------------------------------------------
|          |                                     |        start         |            启动io-all应用          |
|  io-all  |           io-all应用操作            |        stop          |            停止io-all应用          |
|          |                                     |       restart        |            重启io-all应用          |
-------------------------------------------------------------------------------------------------------------
|          |                                     |        start         |            启动ck-puck应用         |
|  ck-puck |           ck-puck应用操作           |        stop          |            停止ck-puck应用         |
|          |                                     |       restart        |            重启ck-puck应用         |
-------------------------------------------------------------------------------------------------------------
|          |                                     |     io-all,branch    |     io-all应用branch分支一条龙     |
|   all    |所有应用源码下载,编译打包到启动一条龙|    ck-puck,branch    |    ck-puck应用branch分支一条龙     |
|          |                                     | ck-puck-front,branch |  ck-puck-front应用branch分支一条龙 |
|          |                                     |      all,branch      |     所有应用branch分支一条龙       |
-------------------------------------------------------------------------------------------------------------
''')

	args = parser.parse_args()

	cls = None
	if args.target != 'all':
		if args.target == 'source':
			app, branch = tuple(input('请输入要获取源码的应用(io-all,ck-puck,ck-puck-front,all)及git分支(以逗号分隔):').split(','))
			cls = SourceExecutable(app, branch)
		elif args.target == 'compile':
			app = input('请输入要编译打包的应用(io-all,ck-puck,ck-puck-front,all):').strip()
			cls = CompileExecutable(app)
		elif args.target == 'redis':
			action = input('请输入要执行的操作(start,stop,restart):').strip()
			cls = RedisExecutable(action)
		elif args.target == 'nginx':
			action = input('请输入要执行的操作(start,stop,restart):').strip()
			cls = NginxExecutable(action)
		elif args.target == 'io-all':
			action = input('请输入要执行的操作(start,stop,restart):').strip()
			cls = IoAllExecutable(action)
		elif args.target == 'ck-puck':
			action = input('请输入要执行的操作(start,stop,restart):').strip()
			cls = CkPuckExecutable(action)

		cls.execute()
	else:
		app, branch = tuple(input('请输入应用(io-all,ck-puck,ck-puck-front,all)及git分支(以逗号分隔):').split(','))
		cls = SourceExecutable(app, branch)
		cls.execute()
		cls = CompileExecutable(app)
		cls.execute()
		if app == 'io-all':
			cls = IoAllExecutable('start')
			cls.execute()
		elif app == 'ck-puck':
			cls = CkPuckExecutable('start')
			cls.execute()
		elif app == 'all':
			cls = IoAllExecutable('start')
			cls.execute()
			cls = CkPuckExecutable('start')
			cls.execute()
