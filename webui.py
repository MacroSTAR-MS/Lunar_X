import os
import json
import requests
import subprocess
import shutil
import zipfile
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
from flask.logging import default_handler
import sys
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PLUGINS_DIR'] = 'plugins'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PLUGINS_DIR'], exist_ok=True)

APPSETTINGS_PATH = os.path.abspath('appsettings.json')
CONFIG_JSON_PATH = os.path.abspath('config.json')
ADMIN_JSON_PATH = os.path.abspath('admin114.json')
WEBUI_JSON_PATH = os.path.abspath('webui.json')

class CustomFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname
        if level == 'INFO':
            level = '\033[94mINFO\033[0m'
        elif level == 'WARNING':
            level = '\033[93mWARNING\033[0m'
        elif level == 'ERROR':
            level = '\033[91mERROR\033[0m'
        return f"[{timestamp}] [Lunar_WebUI] ℹ️ {level} {record.getMessage()}"

handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
app.logger.removeHandler(default_handler)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

def init_default_configs():
    if not os.path.exists(APPSETTINGS_PATH):
        default_appsettings = {
            "$schema": "https://raw.githubusercontent.com/LagrangeDev/Lagrange.Core/master/Lagrange.OneBot/Resources/appsettings_schema.json",
            "Logging": {
                "LogLevel": {
                    "Default": "Information",
                    "Microsoft": "Warning",
                    "Microsoft.Hosting.Lifetime": "Information"
                }
            },
            "SignServerUrl": "https://sign.lagrangecore.org/api/sign/39038",
            "SignProxyUrl": "",
            "MusicSignServerUrl": "",
            "Account": {
                "Uin": 0,
                "Protocol": "Linux",
                "AutoReconnect": True,
                "GetOptimumServer": True
            },
            "Message": {
                "IgnoreSelf": True,
                "StringPost": False
            },
            "QrCode": {
                "ConsoleCompatibilityMode": False
            },
            "Implementations": [
                {
                    "Type": "ForwardWebSocket",
                    "Host": "127.0.0.1",
                    "Port": 3803,
                    "HeartBeatInterval": 5000,
                    "AccessToken": "114514"
                }
            ]
        }
        with open(APPSETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_appsettings, f, indent=2, ensure_ascii=False)
    
    if not os.path.exists(CONFIG_JSON_PATH):
        default_config = {
            "ws_server": "ws://127.0.0.1:3803",
            "token": "114514",
            "bot_qq": 123456789,
            "root_user": 1348472639,
            "log_level": "INFO",
            "trigger_keyword": "$",
            "auto_reload_plugins": True,
            "bot_name": "Lunar X",
            "bot_name_en": "Lunar",
            "answer": [114, 3803, 114514],
            "gemini_key": "",
            "openai_key": "",
            "deepseek_key": ""
        }
        with open(CONFIG_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    if not os.path.exists(ADMIN_JSON_PATH):
        default_admin = {
            "super_users": [987654321],
            "manager_users": [123456789, 987654321, 2473768771]
        }
        with open(ADMIN_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_admin, f, indent=2, ensure_ascii=False)
    
    if not os.path.exists(WEBUI_JSON_PATH):
        default_webui = {
            "use_pypi_mirror": False,
            "pypi_mirror": "https://pypi.tuna.tsinghua.edu.cn/simple",
            "github_mirror": "",
            "github_pat": "",
            "plugins_index_repo": "IntelliMarkets/Jianer_Plugins_Index"
        }
        with open(WEBUI_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_webui, f, indent=2, ensure_ascii=False)
    else:
        with open(WEBUI_JSON_PATH, 'r+', encoding='utf-8') as f:
            webui_config = json.load(f)
            updated = False
            if "github_pat" not in webui_config:
                webui_config["github_pat"] = ""
                updated = True
            if "plugins_index_repo" not in webui_config:
                webui_config["plugins_index_repo"] = "IntelliMarkets/Jianer_Plugins_Index"
                updated = True
            if updated:
                f.seek(0)
                json.dump(webui_config, f, indent=2, ensure_ascii=False)
                f.truncate()

init_default_configs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config/<config_type>', methods=['GET'])
def get_config(config_type):
    try:
        if config_type == 'appsettings':
            with open(APPSETTINGS_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        elif config_type == 'config':
            with open(CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        elif config_type == 'admin':
            with open(ADMIN_JSON_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        elif config_type == 'webui':
            with open(WEBUI_JSON_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            return jsonify({'error': 'Invalid config type'}), 400
        
        return jsonify(config)
    except FileNotFoundError:
        app.logger.error(f"Config file not found for {config_type}.")
        return jsonify({'error': f'Config file not found for {config_type}'}), 404
    except json.JSONDecodeError:
        app.logger.error(f"Invalid JSON in config file for {config_type}.")
        return jsonify({'error': f'Invalid JSON in config file for {config_type}'}), 500
    except Exception as e:
        app.logger.error(f"Error loading config {config_type}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/<config_type>', methods=['POST'])
def update_config(config_type):
    try:
        data = request.get_json()
        
        if config_type == 'appsettings':
            with open(APPSETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif config_type == 'config':
            with open(CONFIG_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif config_type == 'admin':
            with open(ADMIN_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif config_type == 'webui':
            with open(WEBUI_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            return jsonify({'error': 'Invalid config type'}), 400
        
        app.logger.info(f"Config {config_type} updated successfully")
        return jsonify({'message': 'Config updated successfully'})
    except Exception as e:
        app.logger.error(f"Error updating config {config_type}: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_plugins_list():
    plugins = []
    plugins_dir = app.config['PLUGINS_DIR']
    
    if not os.path.exists(plugins_dir):
        return []

    for item in os.listdir(plugins_dir):
        if item == '__pycache__':
            continue
            
        item_path = os.path.join(plugins_dir, item)
        
        is_disabled = item.startswith('d_')
        base_name = item[2:] if is_disabled else item
        
        plugin_type = 'directory'
        if base_name.endswith('.py'):
            plugin_type = 'file'
            base_name = base_name[:-3]

        plugin_info = {
            'name': base_name,
            'full_name': item,
            'enabled': not is_disabled,
            'type': plugin_type
        }
        
        readme_path = None
        if plugin_info['type'] == 'directory':
            readme_path = os.path.join(item_path, 'README.md')
        elif plugin_info['type'] == 'file':
            readme_path = os.path.join(plugins_dir, f"{plugin_info['name']}.md")

        if readme_path and os.path.exists(readme_path):
            plugin_info['has_help'] = True
        else:
            plugin_info['has_help'] = False
        
        plugins.append(plugin_info)
    return plugins

@app.route('/api/plugins', methods=['GET'])
def get_plugins():
    try:
        plugins = get_plugins_list()
        return jsonify(plugins)
    except Exception as e:
        app.logger.error(f"Error getting plugins: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/plugins/<plugin_name>', methods=['GET'])
def get_plugin_details(plugin_name):
    try:
        plugins_dir = app.config['PLUGINS_DIR']
        
        target_path = None
        if os.path.exists(os.path.join(plugins_dir, plugin_name)):
            target_path = os.path.join(plugins_dir, plugin_name)
        elif os.path.exists(os.path.join(plugins_dir, f"{plugin_name}.py")):
            target_path = os.path.join(plugins_dir, f"{plugin_name}.py")
        elif os.path.exists(os.path.join(plugins_dir, f"d_{plugin_name}")):
            target_path = os.path.join(plugins_dir, f"d_{plugin_name}")
        elif os.path.exists(os.path.join(plugins_dir, f"d_{plugin_name}.py")):
            target_path = os.path.join(plugins_dir, f"d_{plugin_name}.py")
        
        if not target_path:
            return jsonify({'error': 'Plugin not found'}), 404
        
        details = {
            'name': plugin_name,
            'type': 'directory' if os.path.isdir(target_path) else 'file'
        }
        
        readme_content = 'No help available'
        if details['type'] == 'directory':
            readme_path = os.path.join(target_path, 'README.md')
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
        elif details['type'] == 'file':
            readme_path = os.path.join(plugins_dir, f"{plugin_name}.md")
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
        
        details['help'] = readme_content
        
        return jsonify(details)
    except Exception as e:
        app.logger.error(f"Error getting plugin details for {plugin_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/plugins/<plugin_name>', methods=['PUT'])
def toggle_plugin(plugin_name):
    try:
        plugins_dir = app.config['PLUGINS_DIR']
        
        current_path = None
        if os.path.exists(os.path.join(plugins_dir, plugin_name)):
            current_path = os.path.join(plugins_dir, plugin_name)
        elif os.path.exists(os.path.join(plugins_dir, f"{plugin_name}.py")):
            current_path = os.path.join(plugins_dir, f"{plugin_name}.py")
        elif os.path.exists(os.path.join(plugins_dir, f"d_{plugin_name}")):
            current_path = os.path.join(plugins_dir, f"d_{plugin_name}")
        elif os.path.exists(os.path.join(plugins_dir, f"d_{plugin_name}.py")):
            current_path = os.path.join(plugins_dir, f"d_{plugin_name}.py")

        if not current_path:
            return jsonify({'error': 'Plugin not found'}), 404

        is_currently_enabled = not os.path.basename(current_path).startswith('d_')

        if is_currently_enabled:
            new_name = f"d_{os.path.basename(current_path)}"
            new_path = os.path.join(plugins_dir, new_name)
            os.rename(current_path, new_path)
            app.logger.info(f"Plugin {plugin_name} disabled")
            return jsonify({'message': 'Plugin disabled successfully'})
        else:
            original_name = os.path.basename(current_path).replace('d_', '')
            original_path = os.path.join(plugins_dir, original_name)
            os.rename(current_path, original_path)
            app.logger.info(f"Plugin {plugin_name} enabled")
            return jsonify({'message': 'Plugin enabled successfully'})
    except Exception as e:
        app.logger.error(f"Error toggling plugin {plugin_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/plugins/<plugin_name>', methods=['DELETE'])
def uninstall_plugin(plugin_name):
    try:
        plugins_dir = app.config['PLUGINS_DIR']
        
        possible_paths = [
            os.path.join(plugins_dir, plugin_name),
            os.path.join(plugins_dir, f"{plugin_name}.py"),
            os.path.join(plugins_dir, f"d_{plugin_name}"),
            os.path.join(plugins_dir, f"d_{plugin_name}.py")
        ]
        
        found_path = None
        for p in possible_paths:
            if os.path.exists(p):
                found_path = p
                break
        
        if not found_path:
            return jsonify({'error': 'Plugin not found'}), 404

        if found_path.endswith('.py') or found_path.endswith('.md'):
            md_path = os.path.join(plugins_dir, f"{plugin_name}.md")
            if os.path.exists(md_path):
                os.remove(md_path)
                app.logger.info(f"Removed associated markdown file: {md_path}")

        if os.path.isdir(found_path):
            shutil.rmtree(found_path)
        else:
            os.remove(found_path)
            
        app.logger.info(f"Plugin {plugin_name} uninstalled")
        return jsonify({'message': 'Plugin uninstalled successfully'})
    except Exception as e:
        app.logger.error(f"Error uninstalling plugin {plugin_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/available_plugins', methods=['GET'])
def get_available_plugins():
    try:
        with open(WEBUI_JSON_PATH, 'r', encoding='utf-8') as f:
            webui_config = json.load(f)
        
        github_mirror = webui_config.get('github_mirror', '').strip()
        github_pat = webui_config.get('github_pat', '').strip()
        plugins_index_repo = webui_config.get('plugins_index_repo', 'IntelliMarkets/Jianer_Plugins_Index')
        
        headers = {}
        if github_pat:
            headers['Authorization'] = f'token {github_pat}'

        github_api_url = f"https://api.github.com/repos/{plugins_index_repo}/contents/"
        
        app.logger.info(f"Fetching available plugins from GitHub API: {github_api_url}")
        response = requests.get(github_api_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                error_msg = "GitHub API 速率限制已超出。请在WebUI配置中填写GitHub个人访问令牌 (PAT) 以提高速率限制。"
                app.logger.error(error_msg)
                return jsonify({'error': error_msg}), 403
            else:
                app.logger.error(f"GitHub API returned status {response.status_code}: {response.text}")
                return jsonify({'error': f'Failed to fetch plugins from GitHub: {response.status_code} - {response.text}'}), 500
        
        items = response.json()
        available_plugins = []
        
        installed_plugins_raw = get_plugins_list() 
        installed_plugin_names = {p['name'] for p in installed_plugins_raw}
        
        for item in items:
            if item['type'] == 'dir':
                plugin_name = item['name']
                
                if plugin_name in installed_plugin_names:
                    continue
                
                raw_zip_url_base = f"https://github.com/{plugins_index_repo}/archive/refs/heads/main.zip"
                plugin_download_url = f"{github_mirror}{raw_zip_url_base}" if github_mirror else raw_zip_url_base

                raw_readme_url_base = f"https://raw.githubusercontent.com/{plugins_index_repo}/main/{plugin_name}/README.md"
                readme_fetch_url = f"{github_mirror}{raw_readme_url_base}" if github_mirror else raw_readme_url_base

                description = "No description available"
                try:
                    readme_response = requests.get(readme_fetch_url, timeout=5)
                    if readme_response.status_code == 200:
                        desc_text = readme_response.text
                        desc_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', desc_text)
                        desc_text = re.sub(r'#+\s*', '', desc_text)
                        desc_text = ' '.join(desc_text.split()).strip()
                        description = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text
                    else:
                        app.logger.warning(f"Could not fetch README for {plugin_name} from {readme_fetch_url}: {readme_response.status_code}")
                except requests.exceptions.RequestException as req_e:
                    app.logger.warning(f"Error fetching README for {plugin_name}: {req_e}")
                except Exception as ex:
                    app.logger.warning(f"Error processing README for {plugin_name}: {ex}")
                
                available_plugins.append({
                    'name': plugin_name,
                    'description': description,
                    'url': plugin_download_url,
                    'path': plugin_name
                })
        
        app.logger.info(f"Found {len(available_plugins)} available plugins")
        return jsonify(available_plugins)
    except Exception as e:
        app.logger.error(f"Error getting available plugins: {str(e)}")
        return jsonify({'error': str(e)}), 500

def _process_plugin_structure(plugin_name, extracted_plugin_root_path, log_callback):
    plugins_dir = app.config['PLUGINS_DIR']
    
    contents_at_root_path = os.listdir(extracted_plugin_root_path)
    if len(contents_at_root_path) == 1 and \
       os.path.isdir(os.path.join(extracted_plugin_root_path, contents_at_root_path[0])) and \
       contents_at_root_path[0] == plugin_name:
        
        nested_dir = os.path.join(extracted_plugin_root_path, plugin_name)
        log_callback(f"检测到嵌套目录 '{nested_dir}'，正在解包...")
        
        for item in os.listdir(nested_dir):
            shutil.move(os.path.join(nested_dir, item), extracted_plugin_root_path)
        shutil.rmtree(nested_dir)
        log_callback(f"嵌套目录 '{nested_dir}' 解包完成。")

    plugin_py_file_in_dir = f"{plugin_name}.py"
    plugin_py_path_in_dir = os.path.join(extracted_plugin_root_path, plugin_py_file_in_dir)
    
    if os.path.exists(plugin_py_path_in_dir):
        current_contents = os.listdir(extracted_plugin_root_path)
        
        significant_contents = [
            item for item in current_contents 
            if item != '__pycache__' and item != plugin_py_file_in_dir
        ]
        
        has_other_py_files = any(f.endswith('.py') for f in significant_contents)
        has_subdirectories = any(os.path.isdir(os.path.join(extracted_plugin_root_path, d)) for d in significant_contents)

        if not has_other_py_files and not has_subdirectories:
            log_callback(f"检测到单文件插件 '{plugin_name}.py'，正在将其移动到插件根目录并处理README。")
            
            shutil.move(plugin_py_path_in_dir, os.path.join(plugins_dir, f"{plugin_name}.py"))
            
            readme_path_in_dir = os.path.join(extracted_plugin_root_path, 'README.md')
            if os.path.exists(readme_path_in_dir):
                shutil.move(readme_path_in_dir, os.path.join(plugins_dir, f"{plugin_name}.md"))
                log_callback(f"重命名并移动 'README.md' 到 '{plugins_dir}/{plugin_name}.md'。")
            
            shutil.rmtree(extracted_plugin_root_path)
            log_callback(f"删除空目录 '{extracted_plugin_root_path}'。")
            
            return

@app.route('/api/plugins', methods=['POST'])
def install_plugin():
    data = request.get_json()
    plugin_url = data.get('url')
    plugin_name = data.get('name')
    plugin_path_in_repo = data.get('path')
    use_pypi_mirror = data.get('use_pypi_mirror', False)
    pypi_mirror = data.get('pypi_mirror', '')
    plugins_index_repo_name_only = data.get('plugins_index_repo_name_only', 'Jianer_Plugins_Index')

    def generate_install_logs():
        def log_progress(msg):
            app.logger.info(f"[Install Progress] {msg}")
            yield f"data: {msg}\n\n"

        zip_path = None
        temp_extract_root = None
        final_plugin_target_dir = None
        
        try:
            if not plugin_url or not plugin_name or not plugin_path_in_repo:
                yield f"data: Error: Missing plugin URL, name, or path\n\n"
                yield f"data: INSTALL_FAILED\n\n"
                return

            yield from log_progress(f"开始下载插件: {plugin_name} from {plugin_url}")
            response = requests.get(plugin_url, stream=True, timeout=60)
            response.raise_for_status()

            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{plugin_name}_repo.zip')
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            yield from log_progress(f"下载中: {downloaded_size}/{total_size} ({percent:.2f}%)")
                        else:
                            yield from log_progress(f"下载中: {downloaded_size} bytes")
            yield from log_progress(f"插件 {plugin_name} 下载完成。")

            plugins_dir = app.config['PLUGINS_DIR']
            final_plugin_target_dir = os.path.join(plugins_dir, plugin_name) 
            temp_extract_root = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_plugin_extract')
            
            os.makedirs(temp_extract_root, exist_ok=True)

            yield from log_progress(f"开始解压插件: {plugin_name}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_root)
            yield from log_progress(f"插件 {plugin_name} 解压完成。")
            
            extracted_repo_root = None
            for item in os.listdir(temp_extract_root):
                if item.startswith(f"{plugins_index_repo_name_only}-"):
                    extracted_repo_root = os.path.join(temp_extract_root, item)
                    break
            
            if not extracted_repo_root:
                dirs_in_temp = [d for d in os.listdir(temp_extract_root) if os.path.isdir(os.path.join(temp_extract_root, d))]
                if len(dirs_in_temp) == 1:
                    extracted_repo_root = os.path.join(temp_extract_root, dirs_in_temp[0])
                else:
                    raise Exception("Could not find the extracted repository root directory.")

            source_plugin_content_dir = os.path.join(extracted_repo_root, plugin_path_in_repo)

            if not os.path.exists(source_plugin_content_dir):
                raise Exception(f"Plugin content directory '{source_plugin_content_dir}' not found in the extracted repository.")

            if os.path.exists(final_plugin_target_dir):
                shutil.rmtree(final_plugin_target_dir)
            os.makedirs(final_plugin_target_dir)

            for item in os.listdir(source_plugin_content_dir):
                shutil.move(os.path.join(source_plugin_content_dir, item), final_plugin_target_dir)
            
            yield from log_progress(f"插件 '{plugin_name}' 内容已移动到临时安装位置 '{final_plugin_target_dir}'。")

            _process_plugin_structure(plugin_name, final_plugin_target_dir, log_progress)

            if os.path.exists(final_plugin_target_dir) and os.path.isdir(final_plugin_target_dir):
                requirements_path = os.path.join(final_plugin_target_dir, 'requirements.txt')
                if os.path.exists(requirements_path):
                    yield from log_progress(f"开始安装插件 {plugin_name} 的依赖...")
                    mirror_cmd = []
                    if use_pypi_mirror and pypi_mirror:
                        mirror_cmd = ['-i', pypi_mirror]
                    
                    process = subprocess.Popen([sys.executable, '-m', 'pip', 'install', '-r', requirements_path] + mirror_cmd, 
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
                    
                    for line in process.stdout:
                        yield from log_progress(f"PIP: {line.strip()}")
                    for line in process.stderr:
                        yield from log_progress(f"PIP ERROR: {line.strip()}")

                    process.wait()

                    if process.returncode != 0:
                        yield from log_progress(f"安装依赖失败，退出码: {process.returncode}")
                        yield f"data: Error: 插件已安装，但依赖安装失败。详情请查看日志。\n\n"
                        yield f"data: INSTALL_FAILED\n\n"
                        return
                    
                    os.remove(requirements_path) 
                    yield from log_progress(f"插件 {plugin_name} 的依赖安装成功。")
                else:
                    yield from log_progress(f"插件 {plugin_name} (目录插件) 没有找到 requirements.txt，跳过依赖安装。")
            else:
                yield from log_progress(f"插件 {plugin_name} (单文件插件) 没有找到 requirements.txt，跳过依赖安装。")
            
            yield from log_progress(f"插件 {plugin_name} 安装成功。")
            yield f"data: INSTALL_SUCCESS\n\n"

        except requests.exceptions.RequestException as req_e:
            error_msg = f"下载插件时发生网络错误: {req_e}"
            app.logger.error(error_msg)
            yield f"data: Error: {error_msg}\n\n"
            yield f"data: INSTALL_FAILED\n\n"
        except Exception as e:
            error_msg = f"安装插件 {plugin_name} 时发生错误: {str(e)}"
            app.logger.error(error_msg)
            yield f"data: Error: {error_msg}\n\n"
            yield f"data: INSTALL_FAILED\n\n"
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
            if temp_extract_root and os.path.exists(temp_extract_root):
                shutil.rmtree(temp_extract_root, ignore_errors=True)

    return Response(stream_with_context(generate_install_logs()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

