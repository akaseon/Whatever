#! /usr/bin/env python
# encoding: utf-8
# WARNING! All changes made to this file will be lost!

import os,shutil,sys,platform
from waflib import TaskGen,Task,Build,Options,Utils,Errors
from waflib.TaskGen import taskgen_method,feature,after_method,before_method
app_info='''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist SYSTEM "file://localhost/System/Library/DTDs/PropertyList.dtd">
<plist version="0.9">
<dict>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleGetInfoString</key>
	<string>Created by Waf</string>
	<key>CFBundleSignature</key>
	<string>????</string>
	<key>NOTE</key>
	<string>THIS IS A GENERATED FILE, DO NOT MODIFY</string>
	<key>CFBundleExecutable</key>
	<string>%s</string>
</dict>
</plist>
'''
def set_macosx_deployment_target(self):
	if self.env['MACOSX_DEPLOYMENT_TARGET']:
		os.environ['MACOSX_DEPLOYMENT_TARGET']=self.env['MACOSX_DEPLOYMENT_TARGET']
	elif'MACOSX_DEPLOYMENT_TARGET'not in os.environ:
		if sys.platform=='darwin':
			os.environ['MACOSX_DEPLOYMENT_TARGET']='.'.join(platform.mac_ver()[0].split('.')[:2])
def create_bundle_dirs(self,name,out):
	bld=self.bld
	dir=out.parent.find_or_declare(name)
	dir.mkdir()
	macos=dir.find_or_declare(['Contents','MacOS'])
	macos.mkdir()
	return dir
def bundle_name_for_output(out):
	name=out.name
	k=name.rfind('.')
	if k>=0:
		name=name[:k]+'.app'
	else:
		name=name+'.app'
	return name
def create_task_macapp(self):
	if self.env['MACAPP']or getattr(self,'mac_app',False):
		out=self.link_task.outputs[0]
		name=bundle_name_for_output(out)
		dir=self.create_bundle_dirs(name,out)
		n1=dir.find_or_declare(['Contents','MacOS',out.name])
		self.apptask=self.create_task('macapp',self.link_task.outputs,n1)
		inst_to=getattr(self,'install_path','/Applications')+'/%s/Contents/MacOS/'%name
		self.bld.install_files(inst_to,n1,chmod=Utils.O755)
		if getattr(self,'mac_resources',None):
			res_dir=n1.parent.parent.make_node('Resources')
			inst_to=getattr(self,'install_path','/Applications')+'/%s/Resources'%name
			for x in self.to_list(self.mac_resources):
				node=self.path.find_resource(x)
				if node:
					rel=node.path_from(self.path)
					tsk=self.create_task('macapp',node,res_dir.make_node(rel))
					self.bld.install_as(inst_to+'/%s'%rel,node)
				else:
					raise Errors.WafError('Missing mac_resource %r in %r'%(x,self))
		if getattr(self.bld,'is_install',None):
			self.install_task.hasrun=Task.SKIP_ME
def create_task_macplist(self):
	if self.env['MACAPP']or getattr(self,'mac_app',False):
		out=self.link_task.outputs[0]
		name=bundle_name_for_output(out)
		dir=self.create_bundle_dirs(name,out)
		n1=dir.find_or_declare(['Contents','Info.plist'])
		self.plisttask=plisttask=self.create_task('macplist',[],n1)
		if getattr(self,'mac_plist',False):
			node=self.path.find_resource(self.mac_plist)
			if node:
				plisttask.inputs.append(node)
			else:
				plisttask.code=self.mac_plist
		else:
			plisttask.code=app_info%self.link_task.outputs[0].name
		inst_to=getattr(self,'install_path','/Applications')+'/%s/Contents/'%name
		self.bld.install_files(inst_to,n1)
def apply_bundle(self):
	if self.env['MACBUNDLE']or getattr(self,'mac_bundle',False):
		self.env['LINKFLAGS_cshlib']=self.env['LINKFLAGS_cxxshlib']=[]
		self.env['cshlib_PATTERN']=self.env['cxxshlib_PATTERN']=self.env['macbundle_PATTERN']
		use=self.use=self.to_list(getattr(self,'use',[]))
		if not'MACBUNDLE'in use:
			use.append('MACBUNDLE')
app_dirs=['Contents','Contents/MacOS','Contents/Resources']
class macapp(Task.Task):
	color='PINK'
	def run(self):
		self.outputs[0].parent.mkdir()
		shutil.copy2(self.inputs[0].srcpath(),self.outputs[0].abspath())
class macplist(Task.Task):
	color='PINK'
	ext_in=['.bin']
	def run(self):
		if getattr(self,'code',None):
			txt=code
		else:
			txt=self.inputs[0].read()
		self.outputs[0].write(txt)

feature('c','cxx')(set_macosx_deployment_target)
taskgen_method(create_bundle_dirs)
feature('cprogram','cxxprogram')(create_task_macapp)
after_method('apply_link')(create_task_macapp)
feature('cprogram','cxxprogram')(create_task_macplist)
after_method('apply_link')(create_task_macplist)
feature('cshlib','cxxshlib')(apply_bundle)
before_method('apply_link','propagate_uselib_vars')(apply_bundle)