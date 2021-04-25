import subprocess
import sys
import os

if sys.platform.lower() == "win32":
    os.system('color')
class color:
    black = lambda x: '\033[30m' + str(x)+'\033[0;39m'
    red = lambda x: '\033[31m' + str(x)+'\033[0;39m'
    green = lambda x: '\033[32m' + str(x)+'\033[0;39m'
    yellow = lambda x: '\033[33m' + str(x)+'\033[0;39m'
    blue = lambda x: '\033[34m' + str(x)+'\033[0;39m'
    magenta = lambda x: '\033[35m' + str(x)+'\033[0;39m'
    cyan = lambda x: '\033[36m' + str(x)+'\033[0;39m'
    white = lambda x: '\033[37m' + str(x)+'\033[0;39m'

def cmd(command):
    result = subprocess.check_output(command)
    return result[:-1].decode('utf-8')

def undo_commit():
    print(color.cyan('Undoing commit: '), end = '')
    result = subprocess.call(['git','reset','HEAD~1','--soft'])
    if int(result)==0:
        print(color.yellow('OK'))
    else:
        print(color.red('FAIL'))

def get_commit_hash():
    return cmd(['git','rev-parse','--verify','HEAD'])

def get_branch_name():
    return cmd(['git','rev-parse','--abbrev-ref','HEAD'])

def extract_branch_name(ref):
    if ref.find('/')<0:
        return ref
    return ref[ref.rfind('/')+1:]

def get_stdin_input():
    for line in sys.stdin:
        if not line.strip():
            continue
        return line.strip().split()
