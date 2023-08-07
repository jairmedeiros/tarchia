import time
from jproperties import Properties
from alive_progress import alive_bar

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

def bold_text(text):
    return '\033[1m' + text + '\033[0m'

def handle_called_process_error(cmd, stderr):
    cmd_string = ' '.join(cmd)

    if 'gradlew' in cmd_string:
        if re.search('java.io.FileNotFoundException', stderr if isinstance(stderr, str) else stderr.decode('utf-8')):
            return  f"\n{bold_text('error:')} gradlew update file wasn't found, maybe dependencies are missing or there is an update since last ant all.\n\nPlease try to run again."

    return f"\n{bold_text('error:')} unknown error, please create an issue with the follow pattern in: https://github.com/jairmedeiros/tarchia/issues/new.\n\n{bold_text('[Title]')}\nCalledProcessError during {cmd_string}\n\n{bold_text('[Description]')}\n#### cmd\n{cmd_string}\n\n#### stacktrace\n```\n{stderr.decode('utf-8')}```"

def git_restore(tag):
    subprocess.run(['git', 'restore', '.'], capture_output=True, check=True)
    subprocess.run(['git', 'tag', '-d', tag], capture_output=True, check=True)

def gradlew():
    current_path = 'gradlew'

    while current_path.count('..') < 8:
        if os.path.exists(current_path):
            return current_path

        current_path = os.path.join('..', current_path)

    raise FileNotFoundError

def build_project(command):
    resources_path = os.path.join('src', 'main', 'resources', 'site-initializer')
    files = set()

    for pattern in (os.path.join(resources_path, '*account*'), os.path.join(resources_path, '*user*')):
        files.update(glob.glob(pattern))

    for file in files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

    subprocess.run([gradlew(), command], capture_output=True, check=True)

def git_checkout_previous():
    subprocess.run(['git', 'checkout', '-'], capture_output=True, check=True)

def get_property_from_file(file_path, key_name):
    properties = Properties()

    with open(file_path, 'rb') as file:
        properties.load(file, 'utf-8')

        data = properties[key_name].data

        if not data:
            raise AttributeError()
        
        return data

def is_tag_built(tag, file_properties_path):
    current_tag_version = None

    try:
        current_tag_version = get_property_from_file(file_path=file_properties_path, key_name='app.server.version.tag')
    except:
        pass

    return current_tag_version == tag

def build_instance(tag, is_tag_built, file_properties_path, no_dxp):
    if not is_tag_built:
        if not no_dxp:
            subprocess.run(['ant', 'setup-profile-dxp', '-S'], capture_output=True, check=True)

        subprocess.run(['ant', 'all', '-S'], capture_output=True, check=True)

        properties = Properties()
        properties['app.server.version.tag'] = tag

        with open(file_properties_path, 'wb') as file:
            properties.store(file, encoding='utf-8')

def git_checkout_tag(origin, tag):
    subprocess.run(['git', 'fetch', origin, 'tag', tag, '--no-tags'], capture_output=True, check=True)
    subprocess.run(['git', 'checkout', tag], capture_output=True, check=True)

def clean_home_dir(exclude):
    for item in os.listdir(os.getcwd()):
        if item != exclude:
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
    
def clean_master_repo(origin, file_path, is_ignore):
    if not is_ignore:
        try:
            subprocess.run(['git', 'checkout', 'master'], capture_output=True, check=True)
        except:
            subprocess.run(['git', 'checkout', '-b', 'master'], capture_output=True, check=True)
    
    subprocess.run(['git', 'fetch', origin, 'master'], capture_output=True, check=True)
    
    if is_ignore:
        subprocess.run(['git', 'rebase', origin + '/master'], capture_output=True, check=True)
    else:
        subprocess.run(['git', 'reset', '--hard', origin + '/master'], capture_output=True, check=True)
    
    subprocess.run(['git', 'clean', '.', '-dfx', '-e', file_path], capture_output=True, check=True)

def get_repo_path(module_path):
    if 'modules' in module_path:
        return os.path.abspath(module_path).split('modules', maxsplit=1)[0]
    
    raise FileNotFoundError

def main():
    parser = argparse.ArgumentParser(prog='tarchia', description='A python script to update Liferay Site Initializers', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('command', help='set the command to be used to build the Site Initializer project')
    parser.add_argument('module', help='set the Site Initializer project module path')

    parser.add_argument('-f', '--force', action='store_true', help='ignore prompts during execution')
    parser.add_argument('-i', '--ignore', action='store_true', help='ignore master reset process')
    parser.add_argument('-o', '--origin', default='upstream', help='set the git origin to fetch new changes from master branch')
    parser.add_argument('-t', '--tag', required=True, help='set tag of Liferay version (eg. 7.4.3.81-ga81)')

    parser.add_argument('--no-dxp', action='store_true', help='disable DXP profile setup before build Liferay instance')

    if len(sys.argv) < 2:
        parser.print_help()

        parser.exit()

    args = parser.parse_args()
    file_properties_path = 'app.server.me.properties'
    file_server_properties_path = 'app.server.version.properties'

    try:
        with alive_bar(file=sys.stderr, monitor=False, stats=False, calibrate=1, ctrl_c=True, spinner=None, receipt=False, dual_line=True) as bar:
            bar.title('Getting repo path from provided module path')
            repo_path = get_repo_path(module_path=args.module)
            print('Repo path found successfully: ' + repo_path, file=sys.stdout)

            bar()
            os.chdir(path=repo_path)

            bar()
            bar.title('Getting app.server.parent.dir value from ' + file_properties_path)
            home_path = get_property_from_file(file_path=file_properties_path, key_name='app.server.parent.dir')
            print('Liferay home found successfully: ' + home_path, file=sys.stdout)

            bar()
            bar.title('Checking if ' + args.tag + ' tag was already built')
            is_built = is_tag_built(tag=args.tag, file_properties_path=file_server_properties_path)
            print('Tag was already built' if is_built else "Tag reference not found", file=sys.stdout)

            bar()
            bar.title('Cleaning and updating repo')
            clean_master_repo(origin=args.origin, file_path=file_properties_path, is_ignore=args.ignore)
            print('repo cleaned and updated successfully and master branch updated', file=sys.stdout)

            bar()
            os.chdir(path=home_path)

            bar()
            bar.title('Cleaning Liferay home')
            clean_home_dir(exclude='portal-setup-wizard.properties')
            print('Liferay home cleaned successfully', file=sys.stdout)

            bar()
            os.chdir(path=repo_path)

            bar()
            git_checkout_tag(origin=args.origin, tag=args.tag)
            print(f'Changed from master branch to {args.tag} tag', file=sys.stdout)

            bar()
            bar.title('Building Liferay instance in ' + args.tag)
            build_instance(tag=args.tag, is_tag_built=is_built, file_properties_path=file_server_properties_path, no_dxp=args.no_dxp)
            print('Instance built successfully', file=sys.stdout)

            bar()
            git_checkout_previous()
            print(f'Changed {args.tag} tag to master branch', file=sys.stdout)

            bar()
            os.chdir(path=args.module)

            bar()
            bar.title('Building project using ' + args.command)
            build_project(command=args.command)
            print('Project built successfully without accounts and users assets', file=sys.stdout)

            bar()
            bar.title('Cleaning up')
            git_restore(tag=args.tag)
            print('Changes restored to master branch', file=sys.stdout)

            bar()
            parser.exit(0, f'Project built successfully to be used with {args.tag} Liferay instance')
    except (KeyError, AttributeError, FileNotFoundError) as error:
        parser.exit(1, f'\nunknown error, please create an issue in: https://github.com/jairmedeiros/tarchia/issues/new.\n\n{str(error)}')
    except subprocess.CalledProcessError as called_process_error:
        parser.exit(called_process_error.returncode, handle_called_process_error(cmd=called_process_error.cmd, stderr=called_process_error.stderr))
    except Exception as error:
        parser.exit(2, f'\nunknown error, please create an issue in: https://github.com/jairmedeiros/tarchia/issues/new.\n\n{str(error)}')

if __name__== '__main__':
    main()
