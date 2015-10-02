import threading, time
import psutil, datetime
import inspect

from flask import Flask
from flask import json
from flask import jsonify

import os.path

app = Flask(__name__)

env_dir = '$HOME/Downloads'
web_port = 8080
get_period = 30

data_list = ['CPU', 'MEM', 'DISK', 'NETIO', 'PROC', 'SYSTEM', ]

data_map = {
	'CPU':['CPU_INFO', 'CPU', ],
	'MEM':['MEM_PHY', 'MEM_SWP', ],
	'DISK':['DISK_INFO', 'DISK', 'DISKIO'],
	'NETIO': ['NETIO', 'SESSION', ], 
	'PROC':['PROC_LIST', ], 
	'SYSTEM':['UPTIME', 'USER_CONN'],
}

@app.route("/")
def index():
	data = {}
	
	data['result'] = 0
	data['info'] = 'This is WT_Agent_H 0.1'
	
	resp = jsonify(data)
	resp.status_code = 200
	
	return resp

@app.route('/info')
def api_info():
    data = {}
    
    data['result'] = 0
    data['message'] = 'result data'
    
    resp = 'This is Error'
    
    try:
    	resp = jsonify(data)
    	resp.status_code = 200
    except Exception, e:
    	data['result'] = -1
    	data['message'] = str(e)
    	
    	print str(e)
    
    return resp

@app.route('/data')
def api_data():
	data = {}
	
	result = {}
	
	for check_type in data_list:
		rsc_list = data_map[check_type]
		
		for check in rsc_list:
			result_data = read_rsc_file(check)
			result[check_type + "." + check] = result_data
	
	data['data'] = result
	data['result'] = 0
	
	try:
		resp = jsonify(data)
		resp.status_code = 200
	except Exception, e:
		data['result'] = -1
		data['message'] = str(e)
		print str(e)
	
	print resp
	
	return resp

@app.route('/data/<data_type>')
def api_data_info(data_type):
	data = {}
	
	result_data = read_rsc_file(data_type)
	
	result = {}
	result[data_type] = result_data
	
	data['result'] = 0
	data['data'] = result
	
	try:
		resp = jsonify(data)
		resp.status_code = 200
	except Exception, e:
		data['result'] = -1
		data['message'] = str(e)
		print str(e)
	
	return resp

def read_rsc_file(file_name):
	list = []
	
	dir = os.path.expandvars(env_dir)
	check_file_name = dir + '/' + file_name
	
	if os.path.isfile(check_file_name):
		try:
			f = open(check_file_name, 'r')
			
			rsc_data = {}
			
			while 1: 
				line = f.readline()
				if not line: break
				
				try:
					tmp = line.split('=')
					
					if len(tmp) != 2:
						pass
					else:
						if tmp[0] == 'rscperf_key':
							if len(rsc_data) != 0:
								list.append(rsc_data)
							
							rsc_data = {}
						
						tmp_data = tmp[1]
						
						len_data = len(tmp_data)
						
						if tmp_data[len_data - 1] == '\n':
							tmp_data = tmp_data[0:len_data-1]
						
						rsc_data[tmp[0]] = tmp_data
				except Exception, e:
					print str(e)
					pass
			
			if len(rsc_data) != 0:
				list.append(rsc_data)
			
			f.close()
		except Exception, e:
			print str(e)
	else:
		list.append('Not Found File : ' + file_name)
	
	return list

def save_rsc_file(file_name, rsc_data_list, is_key):
	dir = os.path.expandvars(env_dir)
	check_file_name = dir + '/' + file_name
	
	f = open(check_file_name, 'w') 
	
	index = 0
	
	for rsc_data in rsc_data_list:
		if is_key:
			f.write('rscperf_key=#' + str(index) + '\n')
		
		for key,value in rsc_data.items():
			f.write(key + "=" + str(value) + '\n')
		
		f.write('\n')
		index = index + 1
	
	f.close()

@app.errorhandler(404)
def not_found(data_type):
	message = {
		'status': 404,
		'message': 'File Not Found: ' + data_type,
	}
	
	resp = jsonify(message)
	resp.status_code = 404
	
	return resp

class WT_Proc_G(threading.Thread):
	thread_id = -1
	
	def run(self):
		options = {
			0 : CPU,
			1 : MEM,
			2 : DISK,
			3 : NETIO,
			4 : PROC,
			5 : SYSTEM,
		}
		
		while (1):
			options[self.thread_id]()
			time.sleep(get_period)
	
def CPU():
	cpu_info = {}
	cpu_info['PROCCESS_COUNT'] = str(psutil.cpu_count(logical=False))
	cpu_info['THREAD_COUNT'] = str(psutil.cpu_count())
	
	save_rsc_file('CPU_INFO', [cpu_info,], False)
	
	cpu_list = []
	
	for cpu_rsc_item in psutil.cpu_times_percent(interval=None, percpu=True):
		cpu_rsc_data = {}
		
		cpu_rsc_data['TOTAL_USERATE'] = cpu_rsc_item.user + cpu_rsc_item.system
		cpu_rsc_data['USER_USERATE'] = cpu_rsc_item.user
		cpu_rsc_data['SYSTEM_USERATE'] = cpu_rsc_item.system
		cpu_rsc_data['IDLE_TIME'] = cpu_rsc_item.idle
		
		try:
			cpu_rsc_data['NICE'] = cpu_rsc_item.nice
		except:
			pass
		
		try:
			cpu_rsc_data['IO_WAIT'] = cpu_rsc_item.iowait
		except:
			pass
		
		try:
			cpu_rsc_data['IRQ'] = cpu_rsc_item.irq
		except:
			pass
		
		try:
			cpu_rsc_data['SOFTIRQ'] = cpu_rsc_item.softirq
		except:
			pass
		
		try:
			cpu_rsc_data['STEAL'] = cpu_rsc_item.steal
		except:
			pass
		
		try:
			cpu_rsc_data['GUEST'] = cpu_rsc_item.guest
		except:
			pass
		
		try:
			cpu_rsc_data['GUEST_NICE'] = cpu_rsc_item.guest_nice
		except:
			pass
		
		cpu_list.append(cpu_rsc_data)
	
	save_rsc_file('CPU', cpu_list, True)

def MEM():
	virtual_memory = psutil.virtual_memory()
	
	virtual_memory_data = {}
	
	virtual_memory_data['total'] = virtual_memory.total
	virtual_memory_data['available'] = virtual_memory.available
	virtual_memory_data['percent'] = virtual_memory.percent
	virtual_memory_data['used'] = virtual_memory.used
	virtual_memory_data['free'] = virtual_memory.free
	
	try:
		virtual_memory_data['active'] = virtual_memory.active
	except:
		pass
	
	try:
		virtual_memory_data['inactive'] = virtual_memory.inactive
	except:
		pass
	
	try:
		virtual_memory_data['buffers'] = virtual_memory.buffers
	except:
		pass
	
	try:
		virtual_memory_data['cached'] = virtual_memory.cached
	except:
		pass
	
	try:
		virtual_memory_data['wired'] = virtual_memory.wired
	except:
		pass
	
	try:
		virtual_memory_data['shared'] = virtual_memory.shared
	except:
		pass
	
	save_rsc_file('MEM_PHY', [virtual_memory_data,], False)
	
	swap_memory = psutil.swap_memory()
	
	swap_memory_data = {}
	
	swap_memory_data['total'] = swap_memory.total
	swap_memory_data['used'] = swap_memory.used
	swap_memory_data['free'] = swap_memory.free
	swap_memory_data['percent'] = swap_memory.percent
	swap_memory_data['sin'] = swap_memory.sin
	swap_memory_data['sout'] = swap_memory.sout
	
	save_rsc_file('MEM_SWP', [swap_memory_data,], False)

def DISK():
	partitions_info_list = []
	partitions_userate_info = []
	
	for disk_partitions in psutil.disk_partitions():
		partitions = {}
		
		partitions['device'] = disk_partitions.device
		partitions['mountpoint'] = disk_partitions.mountpoint
		partitions['fstype'] = disk_partitions.fstype
		partitions['opts'] = disk_partitions.opts
		
		userate_info = psutil.disk_usage(partitions['mountpoint'])
		
		disk_userate = {}
		
		disk_userate['path'] = partitions['mountpoint']
		disk_userate['total'] = userate_info.total
		disk_userate['used'] = userate_info.used
		disk_userate['free'] = userate_info.free
		disk_userate['percent'] = userate_info.percent
		
		partitions_info_list.append(partitions)
		partitions_userate_info.append(disk_userate)
	
	save_rsc_file('DISK_INFO', partitions_info_list, True)
	save_rsc_file('DISK', partitions_userate_info, True)
	
	disk_io_counters_map = psutil.disk_io_counters(perdisk=True)
	
	disk_io_list = []
	
	for key,value in disk_io_counters_map.items():
		disk_io_id = key
		disk_io_counters = value
		
		disk_io_info = {}
		
		disk_io_info['device'] = key		
		disk_io_info['read_count'] = disk_io_counters.read_count
		disk_io_info['write_count'] = disk_io_counters.write_count
		disk_io_info['read_bytes'] = disk_io_counters.read_bytes
		disk_io_info['write_bytes'] = disk_io_counters.write_bytes
		disk_io_info['read_time'] = disk_io_counters.read_time
		disk_io_info['write_time'] = disk_io_counters.write_time
		
		disk_io_list.append(disk_io_info)
	
	save_rsc_file('DISKIO', disk_io_list, True)

def NETIO():
	net_io_counters_map = psutil.net_io_counters(pernic=True)
	
	net_io_list = []
	
	for key,value in net_io_counters_map.items():
		net_io_counters = value
		net_io_data = {}
		
		net_io_data['device'] = key
		net_io_data['bytes_sent'] = net_io_counters.bytes_sent
		net_io_data['bytes_recv'] = net_io_counters.bytes_recv
		net_io_data['packets_sent'] = net_io_counters.packets_sent
		net_io_data['packets_recv'] = net_io_counters.packets_recv
		net_io_data['errin'] = net_io_counters.errin
		net_io_data['errout'] = net_io_counters.errout
		net_io_data['dropin'] = net_io_counters.dropin
		net_io_data['dropout'] = net_io_counters.dropout
		
		net_io_list.append(net_io_data)
	
	save_rsc_file('NETIO', net_io_list, True)
	
	session_list = []
	
	try:
		for session in psutil.net_connections():
		
			session_data = {}
			
			session_data['fd'] = session.fd
			session_data['family'] = session.family
			session_data['type'] = session.type
			session_data['laddr'] = session.laddr
			session_data['raddr'] = session.raddr
			session_data['status'] = session.status
			session_data['pid'] = session.pid
			
			session_list.append(session_data)
	except Exception, e:
		print 'Error : ' + str(e)
	
	save_rsc_file('SESSION', session_list, True)

def PROC():
	process_list = []
	
	for pid in psutil.pids():
		proc_data = {}
		
		process = psutil.Process(pid)
		
		proc_data['pid'] = pid
		proc_data['ppid'] = process.ppid()
		proc_data['name'] = process.name()
		proc_data['create_time'] = process.create_time()
		proc_data['status'] = process.status()
		proc_data['username'] = process.username()
		proc_data['uids'] = process.uids()
		proc_data['gids'] = process.gids()
		proc_data['terminal'] = process.terminal()
		
		try:
			proc_data['exe'] = process.exe()
			proc_data['num_threads'] = process.num_threads()
			proc_data['cpu_times'] = process.cpu_times()
			proc_data['cpu_percent'] = process.cpu_percent()
			proc_data['memory_percent'] = process.memory_percent()
			proc_data['is_running'] = process.is_running()
		except:
			pass
		
		process_list.append(proc_data)
	
	save_rsc_file('PROC_LIST', process_list, True)

def SYSTEM():
	sys_uptime = {}
	sys_uptime['UPTIME'] = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
	sys_uptime['UPTIME_UNIXTIME'] = psutil.boot_time()
	
	save_rsc_file('UPTIME', [sys_uptime, ], False)
	
	user_conn_list = []
		
	for user_conn in psutil.users():
		user_conn_data = {}
		
		user_conn_data['name'] = user_conn.name
		user_conn_data['terminal'] = user_conn.terminal
		user_conn_data['host'] = user_conn.host
		user_conn_data['started'] = user_conn.started
		
		user_conn_list.append(user_conn_data)
	
	save_rsc_file('USER_CONN', user_conn_list, True)
	
def props(obj):
	pr = {}
	
	for name in dir(obj):
		value = getattr(obj, name)
		if not name.startswith('__') and not name.startswith('_') and not inspect.ismethod(value):
			pr[name] = value
	
	return pr

threads = []

if __name__ == "__main__":
	for target in range(len(data_list)):
		th = WT_Proc_G()
		th.thread_id = target
		th.start()
		threads.append(th)
	
	app.run(port=web_port)
