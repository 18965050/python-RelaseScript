#!/home/python35/bin/python
"""
IO项目发布脚本. 选择需要执行的发布命令, 进行不同的发布操作
	source: 获取源文件
	compile: 编译,打包源代码
	nginx: 启动/停止/重启 nginx
	io-all: 启动/停止/重启 io-all应用
	ck-puck: 启动/停止/重启 ck-puck应用

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
source : 下载源代码
compile : 应用编译打包
redis : 启动redis服务
nginx : 启动nginx服务
io-all : 启动io-all应用
ck-puck : 启动ck-puck应用
all : 所有应用从源码下载,编译打包到启动一条龙
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
