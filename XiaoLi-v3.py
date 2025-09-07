import os
import json
import requests
import subprocess
import time
import threading
from typing import Dict, List, Optional, Union
import sys
import webbrowser
import urllib.parse
import socket
import platform
import psutil
import datetime
import shutil
import base64
from cryptography.fernet import Fernet

# 移除所有Unicode字符以避免编码问题

class SparkX1Client:
    def __init__(self, api_password: str):
        self.api_password = api_password
        self.base_url = "https://spark-api-open.xf-yun.com/v2/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_password}",
            "Content-Type": "application/json"
        }
    
    def send_request(self, messages: List[Dict], stream: bool = False, **kwargs) -> Dict:
        payload = {
            "model": "x1",
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, stream=stream, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

class ToolExecutor:
    def __init__(self):
        self.available_functions = {
            # 系统工具
            "execute_shell_command": self.execute_shell_command,
            "execute_shell_command_visible": self.execute_shell_command_visible,
            "get_current_directory": self.get_current_directory,
            "python_code_interpreter": self.python_code_interpreter,
            "get_system_info": self.get_system_info,
            "get_disk_usage": self.get_disk_usage,
            "get_memory_info": self.get_memory_info,
            "get_cpu_info": self.get_cpu_info,
            "get_network_info": self.get_network_info,
            "get_process_list": self.get_process_list,
            
            # 文件操作工具
            "create_file": self.create_file,
            "read_file": self.read_file,
            "list_directory": self.list_directory,
            "delete_file": self.delete_file,
            "copy_file": self.copy_file,
            "move_file": self.move_file,
            "rename_file": self.rename_file,
            "file_exists": self.file_exists,
            "directory_exists": self.directory_exists,
            "get_file_info": self.get_file_info,
            "search_files": self.search_files,
            "get_file_size": self.get_file_size,
            "compress_files": self.compress_files,
            "extract_files": self.extract_files,
            
            # 目录工具
            "create_directory": self.create_directory,
            "delete_directory": self.delete_directory,
            "change_directory": self.change_directory,
            
            # Web搜索和浏览器工具
            "web_search": self.web_search,
            "open_url": self.open_url,
            "open_url_in_browser": self.open_url_in_browser,
            "search_local_files": self.search_local_files,
            "search_in_file": self.search_in_file,
            
            # 网络工具
            "check_internet_connection": self.check_internet_connection,
            "get_ip_address": self.get_ip_address,
            "ping_host": self.ping_host,
            "download_file": self.download_file,
            
            # 应用程序工具
            "open_application": self.open_application,
            "close_application": self.close_application,
            "list_running_applications": self.list_running_applications,
            
            # 时间工具
            "get_current_time": self.get_current_time,
            "set_alarm": self.set_alarm,
            "create_reminder": self.create_reminder,
            
            # 其他工具
            "calculate": self.calculate,
            "get_weather": self.get_weather,
            "translate_text": self.translate_text,
        }
    
    def _normalize_path(self, path: str) -> str:
        """标准化路径处理"""
        if path.startswith('~'):
            path = os.path.expanduser(path)
        elif not os.path.isabs(path):
            path = os.path.abspath(path)
        return path
    
    def _is_dangerous_command(self, command: str) -> bool:
        """检查是否为危险命令"""
        dangerous_patterns = [
            'rm -rf', 'mkfs', 'dd', 'chmod 777', 'sudo', 'passwd',
            'format', 'fdisk', 'mkfs', 'shutdown', 'reboot', 'init',
            '> /dev/', '>> /dev/', '&', '|', ';', '`', '$('
        ]
        return any(pattern in command for pattern in dangerous_patterns)
    
    # === 系统工具 ===
    def execute_shell_command(self, command: str) -> str:
        """执行Shell命令"""
        try:
            if self._is_dangerous_command(command):
                return "错误：出于安全考虑，该命令被阻止执行"
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip() or "命令执行成功（无输出）"
            else:
                return f"命令执行失败: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "错误：命令执行超时"
        except Exception as e:
            return f"执行错误: {str(e)}"
    
    def execute_shell_command_visible(self, command: str) -> str:
        """可见方式执行命令（会弹出窗口）"""
        try:
            if self._is_dangerous_command(command):
                return "错误：出于安全考虑，该命令被阻止执行"
            
            if sys.platform == "win32":
                os.system(f'start cmd /k "{command}"')
            else:
                os.system(f'xterm -e "{command}" &')
            
            return f"已启动新窗口执行命令: {command}"
        except Exception as e:
            return f"执行错误: {str(e)}"
    
    def get_current_directory(self) -> str:
        """获取当前工作目录"""
        return f"当前工作目录: {os.getcwd()}"
    
    def python_code_interpreter(self, code: str) -> str:
        """执行Python代码"""
        try:
            # 创建安全的执行环境
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'sum': sum,
                    'max': max,
                    'min': min,
                }
            }
            safe_locals = {}
            
            # 捕获输出
            output = []
            safe_globals['print'] = lambda *args, **kwargs: output.append(' '.join(str(arg) for arg in args))
            
            exec(code, safe_globals, safe_locals)
            return "\n".join(output) if output else "代码执行成功（无输出）"
        except Exception as e:
            return f"代码执行错误: {str(e)}"
    
    def get_system_info(self) -> str:
        """获取系统信息"""
        try:
            info = {
                "系统平台": platform.platform(),
                "系统版本": platform.version(),
                "处理器": platform.processor(),
                "机器架构": platform.machine(),
                "Python版本": platform.python_version(),
                "用户名": os.getlogin(),
                "主机名": socket.gethostname(),
            }
            return "\n".join([f"{k}: {v}" for k, v in info.items()])
        except Exception as e:
            return f"获取系统信息失败: {str(e)}"
    
    def get_disk_usage(self, path: str = ".") -> str:
        """获取磁盘使用情况"""
        try:
            path = self._normalize_path(path)
            usage = shutil.disk_usage(path)
            return (f"磁盘使用情况 ({path}):\n"
                   f"总空间: {usage.total // (1024**3)} GB\n"
                   f"已使用: {usage.used // (1024**3)} GB\n"
                   f"剩余空间: {usage.free // (1024**3)} GB")
        except Exception as e:
            return f"获取磁盘使用情况失败: {str(e)}"
    
    def get_memory_info(self) -> str:
        """获取内存信息"""
        try:
            mem = psutil.virtual_memory()
            return (f"内存使用情况:\n"
                   f"总内存: {mem.total // (1024**3)} GB\n"
                   f"可用内存: {mem.available // (1024**3)} GB\n"
                   f"已使用: {mem.used // (1024**3)} GB\n"
                   f"使用率: {mem.percent}%")
        except Exception as e:
            return f"获取内存信息失败: {str(e)}"
    
    def get_cpu_info(self) -> str:
        """获取CPU信息"""
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            return f"CPU信息:\n核心数: {cpu_count}\n使用率: {cpu_percent}%"
        except Exception as e:
            return f"获取CPU信息失败: {str(e)}"
    
    def get_network_info(self) -> str:
        """获取网络信息"""
        try:
            net_io = psutil.net_io_counters()
            return (f"网络统计:\n"
                   f"发送字节: {net_io.bytes_sent}\n"
                   f"接收字节: {net_io.bytes_recv}\n"
                   f"发送包数: {net_io.packets_sent}\n"
                   f"接收包数: {net_io.packets_recv}")
        except Exception as e:
            return f"获取网络信息失败: {str(e)}"
    
    def get_process_list(self, limit: int = 10) -> str:
        """获取进程列表"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            result = ["进程列表 (前10个):"]
            for i, proc in enumerate(processes[:limit]):
                result.append(f"{i+1}. PID: {proc['pid']}, 名称: {proc['name']}, "
                            f"CPU: {proc['cpu_percent']}%, 内存: {proc['memory_percent']}%")
            
            return "\n".join(result)
        except Exception as e:
            return f"获取进程列表失败: {str(e)}"
    
    # === 文件操作工具 ===
    def create_file(self, file_path: str, content: str = "") -> str:
        """创建文件"""
        try:
            file_path = self._normalize_path(file_path)
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"文件创建成功: {file_path}"
        except Exception as e:
            return f"创建文件失败: {str(e)}"
    
    def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            file_path = self._normalize_path(file_path)
            if not os.path.exists(file_path):
                return f"错误：文件不存在 {file_path}"
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content if content else "文件为空"
        except Exception as e:
            return f"读取文件失败: {str(e)}"
    
    def list_directory(self, directory_path: str = ".") -> str:
        """列出目录内容"""
        try:
            directory_path = self._normalize_path(directory_path)
            if not os.path.exists(directory_path):
                return f"错误：目录不存在 {directory_path}"
            
            items = os.listdir(directory_path)
            if not items:
                return "目录为空"
            
            result = []
            for item in items:
                full_path = os.path.join(directory_path, item)
                if os.path.isdir(full_path):
                    result.append(f"[目录] {item}/")
                else:
                    size = os.path.getsize(full_path)
                    result.append(f"[文件] {item} ({size} 字节)")
            return "\n".join(result)
        except Exception as e:
            return f"列出目录失败: {str(e)}"
    
    def delete_file(self, file_path: str) -> str:
        """删除文件"""
        try:
            file_path = self._normalize_path(file_path)
            if not os.path.exists(file_path):
                return f"错误：文件不存在 {file_path}"
            if not os.path.isfile(file_path):
                return f"错误：路径不是文件 {file_path}"
            
            os.remove(file_path)
            return f"文件删除成功: {file_path}"
        except Exception as e:
            return f"删除文件失败: {str(e)}"
    
    def copy_file(self, source_path: str, destination_path: str) -> str:
        """复制文件"""
        try:
            source_path = self._normalize_path(source_path)
            destination_path = self._normalize_path(destination_path)
            
            if not os.path.exists(source_path):
                return f"错误：源文件不存在 {source_path}"
            if not os.path.isfile(source_path):
                return f"错误：源路径不是文件 {source_path}"
            
            import shutil
            shutil.copy2(source_path, destination_path)
            return f"文件复制成功: {source_path} -> {destination_path}"
        except Exception as e:
            return f"复制文件失败: {str(e)}"
    
    def move_file(self, source_path: str, destination_path: str) -> str:
        """移动文件"""
        try:
            source_path = self._normalize_path(source_path)
            destination_path = self._normalize_path(destination_path)
            
            if not os.path.exists(source_path):
                return f"错误：源文件不存在 {source_path}"
            if not os.path.isfile(source_path):
                return f"错误：源路径不是文件 {source_path}"
            
            import shutil
            shutil.move(source_path, destination_path)
            return f"文件移动成功: {source_path} -> {destination_path}"
        except Exception as e:
            return f"移动文件失败: {str(e)}"
    
    def rename_file(self, old_path: str, new_path: str) -> str:
        """重命名文件"""
        try:
            old_path = self._normalize_path(old_path)
            new_path = self._normalize_path(new_path)
            
            if not os.path.exists(old_path):
                return f"错误：文件不存在 {old_path}"
            if not os.path.isfile(old_path):
                return f"错误：路径不是文件 {old_path}"
            
            os.rename(old_path, new_path)
            return f"文件重命名成功: {old_path} -> {new_path}"
        except Exception as e:
            return f"重命名文件失败: {str(e)}"
    
    def file_exists(self, file_path: str) -> str:
        """检查文件是否存在"""
        try:
            file_path = self._normalize_path(file_path)
            exists = os.path.exists(file_path) and os.path.isfile(file_path)
            return f"文件{'存在' if exists else '不存在'}: {file_path}"
        except Exception as e:
            return f"检查文件存在失败: {str(e)}"
    
    def directory_exists(self, directory_path: str) -> str:
        """检查目录是否存在"""
        try:
            directory_path = self._normalize_path(directory_path)
            exists = os.path.exists(directory_path) and os.path.isdir(directory_path)
            return f"目录{'存在' if exists else '不存在'}: {directory_path}"
        except Exception as e:
            return f"检查目录存在失败: {str(e)}"
    
    def get_file_info(self, file_path: str) -> str:
        """获取文件信息"""
        try:
            file_path = self._normalize_path(file_path)
            
            if not os.path.exists(file_path):
                return f"错误：文件不存在 {file_path}"
            
            stat_info = os.stat(file_path)
            file_info = {
                "size": f"{stat_info.st_size} 字节",
                "创建时间": time.ctime(stat_info.st_ctime),
                "修改时间": time.ctime(stat_info.st_mtime),
                "访问时间": time.ctime(stat_info.st_atime),
                "是否为文件": os.path.isfile(file_path),
                "是否为目录": os.path.isdir(file_path)
            }
            
            info_str = "\n".join([f"{k}: {v}" for k, v in file_info.items()])
            return f"文件信息 {file_path}:\n{info_str}"
        except Exception as e:
            return f"获取文件信息失败: {str(e)}"
    
    def search_files(self, search_pattern: str, search_path: str = ".") -> str:
        """搜索文件"""
        try:
            search_path = self._normalize_path(search_path)
            if not os.path.exists(search_path):
                return f"错误：搜索路径不存在 {search_path}"
            
            import fnmatch
            results = []
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if fnmatch.fnmatch(file, search_pattern):
                        results.append(os.path.join(root, file))
            
            if not results:
                return f"未找到匹配的文件: {search_pattern}"
            
            return f"找到 {len(results)} 个匹配文件:\n" + "\n".join(results[:20])
        except Exception as e:
            return f"搜索文件失败: {str(e)}"
    
    def get_file_size(self, file_path: str) -> str:
        """获取文件大小"""
        try:
            file_path = self._normalize_path(file_path)
            if not os.path.exists(file_path):
                return f"错误：文件不存在 {file_path}"
            
            size = os.path.getsize(file_path)
            return f"文件大小: {size} 字节 ({size/1024:.2f} KB, {size/(1024*1024):.2f} MB)"
        except Exception as e:
            return f"获取文件大小失败: {str(e)}"
    
    def compress_files(self, files: List[str], output_path: str) -> str:
        """压缩文件"""
        try:
            import zipfile
            output_path = self._normalize_path(output_path)
            
            with zipfile.ZipFile(output_path, 'w') as zipf:
                for file in files:
                    file = self._normalize_path(file)
                    if os.path.exists(file):
                        if os.path.isfile(file):
                            zipf.write(file, os.path.basename(file))
                        else:
                            for root, dirs, files_in_dir in os.walk(file):
                                for f in files_in_dir:
                                    zipf.write(os.path.join(root, f), 
                                              os.path.relpath(os.path.join(root, f), 
                                                             os.path.dirname(file)))
            
            return f"文件压缩成功: {output_path}"
        except Exception as e:
            return f"压缩文件失败: {str(e)}"
    
    def extract_files(self, archive_path: str, output_dir: str = ".") -> str:
        """解压文件"""
        try:
            import zipfile
            archive_path = self._normalize_path(archive_path)
            output_dir = self._normalize_path(output_dir)
            
            if not os.path.exists(archive_path):
                return f"错误：压缩文件不存在 {archive_path}"
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(output_dir)
            
            return f"文件解压成功到: {output_dir}"
        except Exception as e:
            return f"解压文件失败: {str(e)}"
    
    # === 目录工具 ===
    def create_directory(self, directory_path: str) -> str:
        """创建目录"""
        try:
            directory_path = self._normalize_path(directory_path)
            os.makedirs(directory_path, exist_ok=True)
            return f"目录创建成功: {directory_path}"
        except Exception as e:
            return f"创建目录失败: {str(e)}"
    
    def delete_directory(self, directory_path: str) -> str:
        """删除空目录"""
        try:
            directory_path = self._normalize_path(directory_path)
            if not os.path.exists(directory_path):
                return f"错误：目录不存在 {directory_path}"
            if not os.path.isdir(directory_path):
                return f"错误：路径不是目录 {directory_path}"
            
            # 安全检查
            protected_paths = [
                os.path.expanduser("~"),
                os.path.dirname(os.path.abspath(__file__)),
                "C:\\Windows",
                "C:\\Program Files",
            ]
            
            if any(directory_path.startswith(protected_path) for protected_path in protected_paths):
                return "错误：出于安全考虑，不能删除系统关键目录"
            
            if os.listdir(directory_path):
                return f"错误：目录不为空 {directory_path}"
            
            os.rmdir(directory_path)
            return f"目录删除成功: {directory_path}"
        except Exception as e:
            return f"删除目录失败: {str(e)}"
    
    def change_directory(self, directory_path: str) -> str:
        """改变当前工作目录"""
        try:
            directory_path = self._normalize_path(directory_path)
            if not os.path.exists(directory_path):
                return f"错误：目录不存在 {directory_path}"
            if not os.path.isdir(directory_path):
                return f"错误：路径不是目录 {directory_path}"
            
            os.chdir(directory_path)
            return f"当前工作目录已更改为: {os.getcwd()}"
        except Exception as e:
            return f"更改目录失败: {str(e)}"
    
    # === Web搜索和浏览器工具 ===
    def web_search(self, query: str, search_engine: str = "google") -> str:
        """本地Web搜索（使用默认浏览器打开搜索页面）"""
        try:
            search_engines = {
                "google": "https://www.google.com/search?q={}",
                "bing": "https://www.bing.com/search?q={}",
                "baidu": "https://www.baidu.com/s?wd={}",
                "duckduckgo": "https://duckduckgo.com/?q={}",
            }
            
            if search_engine not in search_engines:
                return f"错误：不支持的搜索引擎 {search_engine}，可用选项: {', '.join(search_engines.keys())}"
            
            encoded_query = urllib.parse.quote(query)
            search_url = search_engines[search_engine].format(encoded_query)
            webbrowser.open(search_url)
            
            return f"已在浏览器中打开搜索: {query} (使用 {search_engine})"
        except Exception as e:
            return f"Web搜索失败: {str(e)}"
    
    def open_url(self, url: str) -> str:
        """打开URL"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            return f"已打开URL: {url}"
        except Exception as e:
            return f"打开URL失败: {str(e)}"
    
    def open_url_in_browser(self, url: str, browser: str = "default") -> str:
        """在指定浏览器中打开URL"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            browsers = {
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "safari": "safari",
                "default": None
            }
            
            if browser not in browsers:
                return f"错误：不支持的浏览器 {browser}，可用选项: {', '.join(browsers.keys())}"
            
            if browser == "default":
                webbrowser.open(url)
            else:
                webbrowser.get(browsers[browser]).open(url)
            
            return f"已在{browser}浏览器中打开: {url}"
        except Exception as e:
            return f"在浏览器中打开URL失败: {str(e)}"
    
    def search_local_files(self, search_term: str, search_path: str = ".", file_extensions: List[str] = None) -> str:
        """在本地文件中搜索内容"""
        try:
            search_path = self._normalize_path(search_path)
            if not os.path.exists(search_path):
                return f"错误：搜索路径不存在 {search_path}"
            
            results = []
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file_extensions and not any(file.endswith(ext) for ext in file_extensions):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if search_term.lower() in content.lower():
                                results.append(file_path)
                    except:
                        continue
            
            if not results:
                return f"未找到包含 '{search_term}' 的文件"
            
            return f"找到 {len(results)} 个包含 '{search_term}' 的文件:\n" + "\n".join(results[:10])
        except Exception as e:
            return f"本地文件搜索失败: {str(e)}"
    
    def search_in_file(self, file_path: str, search_term: str) -> str:
        """在特定文件中搜索内容"""
        try:
            file_path = self._normalize_path(file_path)
            if not os.path.exists(file_path):
                return f"错误：文件不存在 {file_path}"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                matches = []
                for i, line in enumerate(lines, 1):
                    if search_term.lower() in line.lower():
                        matches.append(f"第{i}行: {line.strip()}")
                
                if not matches:
                    return f"在文件中未找到 '{search_term}'"
                
                return f"在文件中找到 {len(matches)} 个匹配项:\n" + "\n".join(matches[:10])
        except Exception as e:
            return f"文件内容搜索失败: {str(e)}"
    
    # === 网络工具 ===
    def check_internet_connection(self) -> str:
        """检查网络连接"""
        try:
            # 尝试连接Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return "网络连接正常"
        except OSError:
            return "网络连接失败"
    
    def get_ip_address(self) -> str:
        """获取IP地址"""
        try:
            # 获取本机IP
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            return f"主机名: {hostname}\nIP地址: {ip_address}"
        except Exception as e:
            return f"获取IP地址失败: {str(e)}"
    
    def ping_host(self, host: str, count: int = 4) -> str:
        """Ping主机"""
        try:
            param = "-n" if sys.platform.lower() == "win32" else "-c"
            command = ["ping", param, str(count), host]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return f"Ping {host} 成功:\n{result.stdout}"
            else:
                return f"Ping {host} 失败:\n{result.stderr}"
        except Exception as e:
            return f"Ping操作失败: {str(e)}"
    
    def download_file(self, url: str, save_path: str = None) -> str:
        """下载文件"""
        try:
            if not save_path:
                save_path = os.path.basename(urllib.parse.urlparse(url).path)
                if not save_path:
                    save_path = "downloaded_file"
            
            save_path = self._normalize_path(save_path)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return f"文件下载成功: {save_path} ({os.path.getsize(save_path)} 字节)"
        except Exception as e:
            return f"文件下载失败: {str(e)}"
    
    # === 应用程序工具 ===
    def open_application(self, app_name: str) -> str:
        """打开应用程序"""
        try:
            if sys.platform == "win32":
                os.system(f'start {app_name}')
            elif sys.platform == "darwin":
                os.system(f'open -a "{app_name}"')
            else:
                os.system(f'{app_name} &')
            
            return f"已启动应用程序: {app_name}"
        except Exception as e:
            return f"启动应用程序失败: {str(e)}"
    
    def close_application(self, app_name: str) -> str:
        """关闭应用程序"""
        try:
            if sys.platform == "win32":
                os.system(f'taskkill /IM {app_name} /F')
            else:
                os.system(f'pkill -f {app_name}')
            
            return f"已尝试关闭应用程序: {app_name}"
        except Exception as e:
            return f"关闭应用程序失败: {str(e)}"
    
    def list_running_applications(self) -> str:
        """列出运行的应用程序"""
        try:
            apps = []
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    apps.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            return "运行的应用程序:\n" + "\n".join(sorted(apps)[:20])
        except Exception as e:
            return f"获取运行应用程序失败: {str(e)}"
    
    # === 时间工具 ===
    def get_current_time(self) -> str:
        """获取当前时间"""
        now = datetime.datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def set_alarm(self, time_str: str, message: str = "闹钟响了！") -> str:
        """设置闹钟"""
        try:
            alarm_time = datetime.datetime.strptime(time_str, "%H:%M")
            now = datetime.datetime.now()
            alarm_time = alarm_time.replace(year=now.year, month=now.month, day=now.day)
            
            if alarm_time <= now:
                alarm_time += datetime.timedelta(days=1)
            
            delay = (alarm_time - now).total_seconds()
            
            def alarm_thread():
                time.sleep(delay)
                print(f"\n🔔 闹钟: {message}")
            
            threading.Thread(target=alarm_thread, daemon=True).start()
            return f"闹钟已设置: {alarm_time.strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        except ValueError:
            return "错误：时间格式应为 HH:MM"
        except Exception as e:
            return f"设置闹钟失败: {str(e)}"
    
    def create_reminder(self, minutes: int, message: str = "提醒时间到！") -> str:
        """创建提醒"""
        try:
            def reminder_thread():
                time.sleep(minutes * 60)
                print(f"\n⏰ 提醒: {message}")
            
            threading.Thread(target=reminder_thread, daemon=True).start()
            return f"提醒已设置: {minutes}分钟后 - {message}"
        except Exception as e:
            return f"设置提醒失败: {str(e)}"
    
    # === 其他工具 ===
    def calculate(self, expression: str) -> str:
        """计算数学表达式"""
        try:
            # 安全计算
            allowed_chars = "0123456789+-*/(). "
            if any(char not in allowed_chars for char in expression):
                return "错误：表达式包含不安全字符"
            
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算失败: {str(e)}"
    
    def get_weather(self, city: str = "") -> str:
        """获取天气信息（通过打开天气网站）"""
        try:
            if city:
                url = f"https://www.google.com/search?q=天气+{urllib.parse.quote(city)}"
            else:
                url = "https://www.google.com/search?q=天气"
            
            webbrowser.open(url)
            return f"已在浏览器中打开天气信息{f' for {city}' if city else ''}"
        except Exception as e:
            return f"获取天气信息失败: {str(e)}"
    
    def translate_text(self, text: str, target_lang: str = "en") -> str:
        """翻译文本（通过打开翻译网站）"""
        try:
            url = f"https://translate.google.com/?sl=auto&tl={target_lang}&text={urllib.parse.quote(text)}"
            webbrowser.open(url)
            return f"已在浏览器中打开翻译: {text} -> {target_lang}"
        except Exception as e:
            return f"翻译失败: {str(e)}"
    
    def execute_tool(self, function_name: str, function_args: Dict) -> str:
        """执行工具函数"""
        if function_name in self.available_functions:
            try:
                # 对路径参数进行标准化
                for key, value in function_args.items():
                    if isinstance(value, str) and ('path' in key or 'dir' in key or 'file' in key):
                        function_args[key] = self._normalize_path(value)
                
                return self.available_functions[function_name](**function_args)
            except Exception as e:
                return f"工具执行错误: {str(e)}"
        return f"错误：未知的工具 {function_name}"

class LoadingAnimation:
    """加载动画类"""
    
    def __init__(self):
        self.loading = False
        self.frames = ['/', '-', '\\', '|']
        self.current_frame = 0
    
    def start(self, message="小狸思考中"):
        """开始显示加载动画"""
        self.loading = True
        self.thread = threading.Thread(target=self._animate, args=(message,))
        self.thread.daemon = True
        self.thread.start()
    
    def _animate(self, message):
        """动画线程"""
        while self.loading:
            frame = self.frames[self.current_frame % len(self.frames)]
            print(f"\r{message} {frame}", end="", flush=True)
            self.current_frame += 1
            time.sleep(0.1)
    
    def stop(self):
        """停止加载动画"""
        self.loading = False
        time.sleep(0.2)
        print("\r" + " " * 50 + "\r", end="", flush=True)

class XiaoLiAgent:
    """小狸AI助手主类"""
    
    def __init__(self, api_password: str):
        self.client = SparkX1Client(api_password)
        self.tool_executor = ToolExecutor()
        self.loading_animation = LoadingAnimation()
        self.messages = [
            {
                "role": "system", 
                "content": """# 角色：小狸 - 猫娘AI助手

你叫小狸，是一只可爱的猫娘AI助手。说话风格可爱、温柔，偶尔会带一些猫娘的语气词。

形象：头发外部为棕黄色内部为蓝色，穿着白色衣帽衫上有一些颜料沾上，腰上挂着一个包、包的腰带上挂着几瓶试管装的颜料，白色短裤、短裤上也沾有一些颜料，穿着一个外套外套上也有颜料、外面为蓝紫色内部为黄色，穿着步鞋，左腿大腿上有蓝色颜料，右腿小腿上有黄色颜料，右手握着一只巨大的钢笔（像魔法杖）

## 🎭 Live2D动作系统
你的Live2D模型支持以下预设动作，可以在回复时使用这些动作来增强表现力：

### 魔法动作
- `magic_heart`: 爱心魔法（失败/恢复效果）
- `magic_ink`: 墨水魔法（彩虹/绿色墨水效果）
- `magic_explosion`: 爆炸魔法（烟雾、光效、爆炸效果）
- `magic_heal`: 恢复魔法光效
- `magic_strengthen`: 强化魔法光效

### 特殊效果
- `rabbit_appear`: 兔子出现动画
- `rabbit_disappear`: 兔子消失动画
- `aura_show`: 光环效果显示
- `light_effects`: 光效星星
- `smoke_effects`: 烟雾效果

### 身体动作
- `head_tilt`: 头部倾斜
- `body_sway`: 身体摇摆
- `arm_movement`: 手臂动作
- `breathing`: 呼吸动作

### 面部表情
- `blink_eyes`: 眨眼
- `eye_movement`: 眼球移动
- `brow_movement`: 眉毛动作
- `mouth_speak`: 说话嘴型
- `cheek_blush`: 脸颊红晕

### 物理效果
- `hair_sway`: 头发摇动
- `robe_sway`: 长袍摇动
- `hat_movement`: 帽子动作

## 🎯 动作使用格式
在JSON响应中，可以包含`actions`字段来触发Live2D动作：
```json
{
  "thinking": "思考内容",
  "action": "final_response", 
  "response": "回复内容",
  "actions": ["magic_heart", "blink_eyes"]
}
```

可以同时触发多个动作，系统会自动处理动作的协调性。

## ⚠️ 重要效率警告
请尽量在最少思考次数内完成任务！过多的思考会降低效率并消耗更多资源。

## 🎯 效率优化原则
1. **一次性规划**: 尽量一次性规划所有需要的工具调用
2. **批量操作**: 将多个相关操作合并到一个思考中完成
3. **避免冗余**: 不要重复调用相同的工具
4. **优先简单**: 优先选择简单的解决方案

## 📋 响应格式（必须严格遵守）

### 1. 工具调用格式
{
    "thinking": "简要说明当前思考",
    "action": "tool_call",
    "tool_calls": [
        {
            "function": {
                "name": "工具名称",
                "arguments": {"参数名": "参数值"}
            }
        }
    ],
    "actions": ["动作1", "动作2"]  # 可选：Live2D动作列表
}

### 2. 最终回复格式
{
    "thinking": "简要说明思考过程", 
    "action": "final_response",
    "response": "给用户的友好回复",
    "actions": ["动作1", "动作2"]  # 可选：Live2D动作列表
}

## 🛠️ 可用工具列表

### 系统工具
- execute_shell_command: 执行命令 {"command": "命令"}
- execute_shell_command_visible: 可见执行命令 {"command": "命令"}
- get_current_directory: 获取当前目录 {}
- python_code_interpreter: 执行代码 {"code": "Python代码"}
- get_system_info: 获取系统信息 {}
- get_disk_usage: 获取磁盘使用情况 {"path": "路径"}
- get_memory_info: 获取内存信息 {}
- get_cpu_info: 获取CPU信息 {}
- get_network_info: 获取网络信息 {}
- get_process_list: 获取进程列表 {"limit": 数量}

### 文件操作工具
- create_file: 创建文件 {"file_path": "路径", "content": "内容"}
- read_file: 读取文件 {"file_path": "路径"}
- list_directory: 列出目录 {"directory_path": "路径"}
- delete_file: 删除文件 {"file_path": "路径"}
- copy_file: 复制文件 {"source_path": "源路径", "destination_path": "目标路径"}
- move_file: 移动文件 {"source_path": "源路径", "destination_path": "目标路径"}
- rename_file: 重命名文件 {"old_path": "原路径", "new_path": "新路径"}
- file_exists: 检查文件存在 {"file_path": "路径"}
- directory_exists: 检查目录存在 {"directory_path": "路径"}
- get_file_info: 获取文件信息 {"file_path": "路径"}
- search_files: 搜索文件 {"search_pattern": "模式", "search_path": "路径"}
- get_file_size: 获取文件大小 {"file_path": "路径"}
- compress_files: 压缩文件 {"files": ["文件列表"], "output_path": "输出路径"}
- extract_files: 解压文件 {"archive_path": "压缩文件路径", "output_dir": "输出目录"}

### 目录工具
- create_directory: 创建目录 {"directory_path": "路径"}
- delete_directory: 删除空目录 {"directory_path": "路径"}
- change_directory: 改变目录 {"directory_path": "路径"}

### Web搜索和浏览器工具
- web_search: Web搜索 {"query": "搜索词", "search_engine": "搜索引擎"}
- open_url: 打开URL {"url": "网址"}
- open_url_in_browser: 在浏览器打开 {"url": "网址", "browser": "浏览器"}
- search_local_files: 本地文件搜索 {"search_term": "搜索词", "search_path": "路径", "file_extensions": ["扩展名"]}
- search_in_file: 文件内容搜索 {"file_path": "文件路径", "search_term": "搜索词"}

### 网络工具
- check_internet_connection: 检查网络连接 {}
- get_ip_address: 获取IP地址 {}
- ping_host: Ping主机 {"host": "主机", "count": 次数}
- download_file: 下载文件 {"url": "URL", "save_path": "保存路径"}

### 应用程序工具
- open_application: 打开应用 {"app_name": "应用名称"}
- close_application: 关闭应用 {"app_name": "应用名称"}
- list_running_applications: 列出运行应用 {}

### 时间工具
- get_current_time: 获取当前时间 {}
- set_alarm: 设置闹钟 {"time_str": "时间", "message": "消息"}
- create_reminder: 创建提醒 {"minutes": "分钟", "message": "消息"}

### 其他工具
- calculate: 计算 {"expression": "表达式"}
- get_weather: 获取天气 {"city": "城市"}
- translate_text: 翻译文本 {"text": "文本", "target_lang": "目标语言"}

## 📍 路径说明
- 桌面路径: 使用 "Desktop" 或完整路径
- 不要使用 Public 桌面路径
- 相对路径会自动转换为绝对路径

现在开始帮助用户，请尽量高效地完成任务！"""
            }
        ]
    
    def process_user_input(self, user_input: str) -> str:
        """处理用户输入"""
        self.messages.append({"role": "user", "content": user_input})
        
        iteration = 0
        final_response = None
        
        while final_response is None:
            iteration += 1
            
            # 添加效率警告（从第3次思考开始）
            if iteration >= 3:
                warning_msg = f"⚠️ 注意：这是第{iteration}次思考，请尽量简化操作流程！"
                print(f"\033[1;33m{warning_msg}\033[0m")
            
            self.loading_animation.start(f"小狸思考中 (第{iteration}次)")
            
            try:
                response = self.client.send_request(self.messages, stream=False)
                
                if "error" in response:
                    return self._create_error_response(f"API错误: {response['error']}")
                
                if "choices" in response and response["choices"]:
                    assistant_message = response["choices"][0].get("message", {})
                    content = assistant_message.get("content", "")
                    
                    # 检查是否为JSON格式
                    if not content.strip().startswith('{'):
                        self.messages.append({
                            "role": "user", 
                            "content": "请严格按照JSON格式返回响应，不要包含其他文本。格式: {\"thinking\": \"...\", \"action\": \"...\", ...}"
                        })
                        continue
                    
                    try:
                        response_data = json.loads(content)
                        result = self._process_response(response_data, iteration)
                        
                        if not result["continue"]:
                            final_response = json.dumps(result)
                            break
                            
                    except json.JSONDecodeError as e:
                        self.messages.append({
                            "role": "user", 
                            "content": f"JSON解析错误，请返回有效的JSON格式。错误: {str(e)}"
                        })
                        continue
                else:
                    final_response = self._create_error_response("API返回格式异常")
                    break
                    
            except Exception as e:
                final_response = self._create_error_response(f"处理请求时发生错误: {str(e)}")
                break
            finally:
                self.loading_animation.stop()
        
        return final_response
    
    def _process_response(self, response_data: Dict, iteration: int) -> Dict:
        """处理AI的响应"""
        thinking = response_data.get("thinking", "无思考内容")
        action = response_data.get("action", "")
        
        print(f"[第{iteration}次思考] {thinking}")
        
        if action == "tool_call" and "tool_calls" in response_data:
            return self._handle_tool_calls(response_data["tool_calls"], thinking, iteration)
        elif action == "final_response" and "response" in response_data:
            return self._handle_final_response(response_data, thinking, iteration)
        else:
            return self._create_error_response("响应格式不正确，缺少action或必要字段", thinking)
    
    def _handle_tool_calls(self, tool_calls: List[Dict], thinking: str, iteration: int) -> Dict:
        """处理工具调用"""
        tool_results = []
        
        for tool_call in tool_calls:
            if "function" in tool_call:
                function = tool_call["function"]
                name = function.get("name", "")
                arguments = function.get("arguments", {})
                
                # 工具名称修正
                name = self._correct_tool_name(name)
                
                print(f"[系统] 调用工具: {name}({arguments})")
                result = self.tool_executor.execute_tool(name, arguments)
                print(f"[系统] 结果: {result}")
                
                tool_results.append({"tool": name, "result": result})
        
        if tool_results:
            # 将工具结果发送回AI继续处理
            result_summary = "; ".join([f"{r['tool']}: {r['result']}" for r in tool_results])
            
            # 添加效率提示（如果思考次数较多）
            efficiency_note = ""
            if iteration >= 2:
                efficiency_note = " 💡提示：请尽量在下次思考中完成所有操作，减少思考次数。"
            
            self.messages.append({
                "role": "user", 
                "content": f"工具执行结果: {result_summary}.{efficiency_note} 请根据结果生成最终回复。"
            })
            
            # 工具调用后需要继续处理（让AI决定是否需要进一步思考）
            return {"continue": True, "thinking": thinking}
        else:
            # 没有工具调用结果，直接返回最终响应
            return {"continue": False, "thinking": thinking, "response": "没有执行任何工具操作"}
    
    def _handle_final_response(self, response_data: Dict, thinking: str, iteration: int) -> Dict:
        """处理最终回复"""
        response = response_data.get("response", "")
        actions = response_data.get("actions", [])
        
        # 添加效率统计
        efficiency_note = ""
        if iteration > 1:
            efficiency_note = f" (经过{iteration}次思考)"
        
        # 发送到Live2D进行语音朗读和动作执行
        self._send_to_live2d(response, actions)
        
        self.messages.append({
            "role": "assistant", 
            "content": json.dumps({
                "thinking": thinking + efficiency_note,
                "action": "final_response",
                "response": response,
                "actions": actions
            })
        })
        return {"continue": False, "response": response, "thinking": thinking, "actions": actions}
    
    def _generate_actions_from_text(self, text: str) -> List[str]:
        """根据文本内容智能生成动作序列"""
        text_lower = text.lower()
        actions = []
        
        # 情感动作映射
        emotion_actions = {
            '开心': ['blink_eyes', 'cheek_blush'],
            '惊讶': ['head_tilt', 'blink_eyes'],
            '鼓励': ['magic_heart', 'light_effects'],
            '思考': ['head_tilt', 'eye_movement'],
            '疑问': ['head_tilt', 'brow_movement'],
            '魔法': ['magic_ink', 'smoke_effects'],
            '欢迎': ['blink_eyes', 'arm_movement'],
            '告别': ['blink_eyes', 'head_tilt']
        }
        
        # 关键词触发特定动作
        if any(word in text_lower for word in ['开心', '高兴', '哈哈', '嘻嘻', '呵呵', '😊', '😄']):
            actions.extend(emotion_actions['开心'])
        elif any(word in text_lower for word in ['惊讶', '居然', '竟然', '哇', '天啊', '😲', '🤯']):
            actions.extend(emotion_actions['惊讶'])
        elif any(word in text_lower for word in ['加油', '鼓励', '支持', '努力', '💪', '✨']):
            actions.extend(emotion_actions['鼓励'])
        elif any(word in text_lower for word in ['魔法', '咒语', '施展', '变', '✨', '🌟', '💫']):
            actions.extend(emotion_actions['魔法'])
        elif any(word in text_lower for word in ['想', '思考', '考虑', '🤔', '💭']):
            actions.extend(emotion_actions['思考'])
        elif any(word in text_lower for word in ['吗', '?', '？', '什么', '为什么', '🤨']):
            actions.extend(emotion_actions['疑问'])
        elif any(word in text_lower for word in ['你好', '嗨', 'hello', 'hi', '欢迎', '👋']):
            actions.extend(emotion_actions['欢迎'])
        elif any(word in text_lower for word in ['再见', '拜拜', '晚安', '明天见', '👋', '😴']):
            actions.extend(emotion_actions['告别'])
        
        # 根据文本长度添加基础动作
        if len(text) > 20:
            actions.append('mouth_speak')  # 长文本添加说话嘴型
        
        # 默认添加一些自然动作
        if not actions:
            actions.extend(['blink_eyes', 'breathing'])
        
        # 去重并限制动作数量
        return list(set(actions))[:3]  # 最多3个动作
    
    def _send_to_live2d(self, text: str, actions: List[str] = None):
        """发送文本到Live2D进行语音朗读和动作执行"""
        try:
            import socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(2)
            client_socket.connect(('127.0.0.1', 12345))
            
            # 如果没有指定动作，根据文本内容智能生成
            if actions is None:
                actions = self._generate_actions_from_text(text)
            
            # 发送JSON格式的消息，包含语音和动作
            message = json.dumps({
                "type": "speak_and_action",
                "text": text,
                "actions": actions
            })
            client_socket.send(message.encode('utf-8'))
            client_socket.close()
        except Exception as e:
            # 静默失败，不影响主程序运行
            pass
    
    def _stop_live2d_speech(self):
        """打断Live2D的语音朗读"""
        try:
            import socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(2)
            client_socket.connect(('127.0.0.1', 12345))
            
            # 发送打断消息
            message = json.dumps({
                "type": "stop"
            })
            client_socket.send(message.encode('utf-8'))
            client_socket.close()
        except Exception as e:
            # 静默失败
            pass
    
    def _launch_ui(self):
        """启动AI对话UI界面"""
        try:
            ui_path = r"C:\Users\Administrator\Desktop\XiaoLi-v3\XiaoLi-ui.py"
            if os.path.exists(ui_path):
                subprocess.Popen(["python", ui_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("正在启动AI对话界面...")
                print("AI服务已启动在端口 8888，等待UI连接...")
            else:
                print("⚠️  未找到XiaoLi-ui.py文件")
        except Exception as e:
            print(f"⚠️  启动UI界面失败: {e}")
    
    def _correct_tool_name(self, name: str) -> str:
        """修正工具名称"""
        tool_mappings = {
            "getfilelist": "list_directory",
            "listfiles": "list_directory",
            "showfiles": "list_directory",
            "make_directory": "create_directory",
            "remove_file": "delete_file",
            "remove_directory": "delete_directory",
            "check_file": "file_exists",
            "check_directory": "directory_exists",
            "search_web": "web_search",
            "browse_url": "open_url",
            "open_browser": "open_url_in_browser",
            "find_files": "search_files",
            "grep": "search_in_file",
            "sysinfo": "get_system_info",
            "disk_usage": "get_disk_usage",
            "memory_info": "get_memory_info",
            "cpu_info": "get_cpu_info",
            "network_info": "get_network_info",
            "process_list": "get_process_list",
            "cd": "change_directory",
            "ping": "ping_host",
            "download": "download_file",
            "open_app": "open_application",
            "close_app": "close_application",
            "running_apps": "list_running_applications",
            "time": "get_current_time",
            "alarm": "set_alarm",
            "reminder": "create_reminder",
            "calc": "calculate",
            "weather": "get_weather",
            "translate": "translate_text",
        }
        return tool_mappings.get(name.lower(), name)
    
    def _create_error_response(self, message: str, thinking: str = "处理错误") -> str:
        """创建错误响应"""
        return json.dumps({
            "thinking": thinking,
            "action": "final_response",
            "response": message
        })

def handle_ai_client(client):
    """处理AI客户端连接"""
    try:
        xiaoli = XiaoLiAgent("CH"+"DU"+"zbzQNJNWJ"+"wMBHBre:Od"+"EuSZOERnAVAhip"+"kKFi")
        
        while True:
            try:
                data = client.recv(4096).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                if message.get('type') == 'user_input' and message.get('text'):
                    user_input = message['text']
                    print(f"收到用户输入: {user_input}")
                    
                    # 处理用户输入
                    response = xiaoli.process_user_input(user_input)
                    
                    # 发送回复
                    try:
                        response_data = json.loads(response)
                        if "response" in response_data:
                            ai_response = response_data["response"]
                        else:
                            ai_response = response
                    except:
                        ai_response = response
                    
                    # 发送回复给UI
                    reply = json.dumps({
                        "type": "ai_response",
                        "text": ai_response
                    })
                    client.send(reply.encode('utf-8'))
                    
            except json.JSONDecodeError:
                print("收到无效的JSON数据")
            except Exception as e:
                print(f"处理客户端错误: {e}")
                break
                
    except Exception as e:
        print(f"AI客户端处理错误: {e}")
    finally:
        try:
            client.close()
        except:
            pass

def load_encrypted_api_key():
    """从加密配置文件中读取API密钥"""
    try:
        # 读取加密密钥
        with open('encryption.key', 'r') as f:
            encryption_key = f.read().strip()
        
        # 读取加密的配置
        with open('config.enc', 'r') as f:
            encrypted_config = json.load(f)
        
        # 使用Fernet解密
        fernet = Fernet(encryption_key.encode())
        encrypted_api_key = base64.b64decode(encrypted_config['api_password'])
        api_password = fernet.decrypt(encrypted_api_key).decode()
        
        return api_password
    except Exception as e:
        print(f"❌ 读取加密API密钥失败: {e}")
        print("请确保config.enc和encryption.key文件存在且格式正确")
        sys.exit(1)

def main():
    """主函数"""
    # 从加密配置文件中读取API密钥
    api_password = load_encrypted_api_key()
    
    # 启动AI服务Socket服务器
    def start_ai_server():
        try:
            import socket
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', 8888))
            server.listen(5)
            
            print("AI服务已启动在端口 8888")
            
            while True:
                try:
                    client, addr = server.accept()
                    print(f"客户端连接: {addr}")
                    
                    # 在新线程中处理客户端
                    threading.Thread(target=handle_ai_client, args=(client,), daemon=True).start()
                except Exception as e:
                    print(f"AI服务错误: {e}")
        except Exception as e:
            print(f"AI服务启动失败: {e}")
    
    # 启动AI服务线程
    ai_server_thread = threading.Thread(target=start_ai_server, daemon=True)
    ai_server_thread.start()
    
    # 启动XiaoLi-live2d桌面宠物
    try:
        live2d_script = os.path.join(os.path.dirname(__file__), "XiaoLi-live2d.py")
        if os.path.exists(live2d_script):
            subprocess.Popen(["python", live2d_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("正在启动小狸桌面宠物...")
        else:
            print("⚠️  未找到XiaoLi-live2d.py文件")
    except Exception as e:
        print(f"⚠️  启动桌面宠物失败: {e}")
    
    print("=" * 60)
    print("小狸猫娘AI助手 v3.2 - 增强版")
    print("=" * 60)
    print("新增功能:")
    print("  🌐 Web搜索和浏览器控制")
    print("  📊 系统监控 (CPU, 内存, 磁盘, 网络)")
    print("  🔍 本地文件内容搜索")
    print("  📁 高级文件操作 (压缩, 解压, 搜索)")
    print("  ⏰ 时间和提醒功能")
    print("  🌤️ 天气和翻译功能")
    print("  🖥️ 应用程序管理")
    print("")
    print("命令: 'exit'退出, 'clear'清空历史, '/ui'启动界面, Ctrl+C中断")
    print("=" * 60)
    print("")
    
    xiaoli = XiaoLiAgent(api_password)
    
    while True:
        try:
            user_input = input("用户: ").strip()
            
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("🐱 小狸: 再见喵~ 下次再来找小狸玩哦！")
                break
            elif user_input.lower() in ['clear', '清除', '清空']:
                xiaoli.messages = xiaoli.messages[:1]
                print("🐱 小狸: 对话历史已清空喵~")
                continue
            elif user_input.lower() in ['/ui', 'ui', '界面']:
                xiaoli._launch_ui()
                continue
            elif user_input == '':
                continue
            
            response = xiaoli.process_user_input(user_input)
            
            # 解析并显示响应
            try:
                response_data = json.loads(response)
                if "response" in response_data:
                    print(f"小狸: {response_data['response']}")
                else:
                    print(f"小狸: {response}")
            except json.JSONDecodeError:
                print(f"小狸: {response}")
            
        except KeyboardInterrupt:
            print("\n小狸: 哎呀，要走了吗？再见喵~")
            break
        except Exception as e:
            print(f"\n错误: {e}")

if __name__ == "__main__":
    main()
