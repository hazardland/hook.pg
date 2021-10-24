import subprocess
import sys
import os
import socket

if sys.platform.lower() == "win32":
    os.system('color')

# for i in list(range(31,37))+list(range(91,97)): print("\033["+str(i)+"m\\033["+str(i)+"m TEXT \\033[0;39m\033[0;39m")

class color:
    black = lambda x: '\033[30m' + str(x)+'\033[0;39m'
    red = lambda x: '\033[31m' + str(x)+'\033[0;39m'
    green = lambda x: '\033[32m' + str(x)+'\033[0;39m'
    yellow = lambda x: '\033[33m' + str(x)+'\033[0;39m'
    blue = lambda x: '\033[34m' + str(x)+'\033[0;39m'
    magenta = lambda x: '\033[35m' + str(x)+'\033[0;39m'
    cyan = lambda x: '\033[36m' + str(x)+'\033[0;39m'
    white = lambda x: '\033[37m' + str(x)+'\033[0;39m'
    lime = lambda x: '\033[92m' + str(x)+'\033[0;39m'
    pink = lambda x: '\033[95m' + str(x)+'\033[0;39m'

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

# This function will provide env variables for requested server type
def pg_env(pg_server_type, pg_target_db):

    if pg_target_db:
        pg_target_db = pg_target_db.strip()

    if pg_server_type=='pg_branch':
        pg_master_database = os.getenv('PG_MASTER_DATABASE')
        pg_master_server = os.getenv('PG_MASTER_SERVER')
        pg_target_db_copy = pg_target_db
        pg_target_db = ""
        if pg_master_server != '':
            pg_target_db = pg_master_server + '_'
        if pg_master_database != '':            
            pg_target_db = pg_target_db + pg_master_database + '_'
        pg_target_db = pg_target_db + pg_target_db_copy    
        return (socket.gethostbyname(os.getenv('PG_BRANCH_HOSTNAME')),
            os.getenv('PG_BRANCH_PORT'),
            os.getenv('PG_BRANCH_PASSWORD'),
            os.getenv('PG_BRANCH_USERNAME'),
            pg_target_db)
    if pg_server_type=='pg_master':
        pg_target_db = os.getenv('PG_MASTER_DATABASE')
        return (socket.gethostbyname(os.getenv('PG_MASTER_HOSTNAME')),
            os.getenv('PG_MASTER_PORT'),
            os.getenv('PG_MASTER_PASSWORD'),
            os.getenv('PG_MASTER_USERNAME'),
            pg_target_db)
    if pg_server_type=='pg_staging':
        pg_target_db = os.getenv('PG_STAGING_DATABASE')
        return (socket.gethostbyname(os.getenv('PG_STAGING_HOSTNAME')),
            os.getenv('PG_STAGING_PORT'),
            os.getenv('PG_STAGING_PASSWORD'),
            os.getenv('PG_STAGING_USERNAME'),
            pg_target_db)
    if pg_server_type=='pg_dev':
        return (socket.gethostbyname(os.getenv('PG_DEV_HOSTNAME')),
        os.getenv('PG_DEV_PORT'),
        os.getenv('PG_DEV_PASSWORD').replace("\"", "\\\""),
        os.getenv('PG_DEV_USERNAME'),
        pg_target_db)

    raise Exception('unknown_env')

# The function is used for diff generation and diff apply
def pg_sync(pg_from_env, 
                   pg_to_env, 
                   pg_from_db, 
                   pg_to_db, 
                   pg_sql_file,
                   pg_apply=False,
                   pg_create_from_db=False, 
                   pg_create_to_db=False):

        pg_from_hostname, pg_from_port, pg_from_password, pg_from_username, pg_from_db = pg_env(pg_from_env, pg_from_db)
        pg_to_hostname, pg_to_port, pg_to_password, pg_to_username, pg_to_db = pg_env(pg_to_env, pg_to_db)
  
        print(color.cyan('From db: '), color.yellow(pg_from_db)+color.green('@'+pg_from_env))
        print(color.cyan('To db: '), color.yellow(pg_to_db)+color.green('@'+pg_to_env))

        print(color.cyan('Sql file is '+pg_sql_file))

        if pg_create_to_db:
            print('Checking target db '+pg_to_db+'@'+pg_to_env+'...')
            try:
                subprocess.call(['psql',f'postgresql://{pg_to_username}:{pg_to_password}@{pg_to_hostname}:{pg_to_port}/', 
                    '-c', f'CREATE DATABASE {pg_to_db}'],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except:
                pass

        #print(f'postgresql://{pg_to_username}:{pg_to_password}@{pg_to_hostname}:{pg_to_port}/{pg_to_db}')

        # I did not remember why is this there (?)
        if not pg_from_db:
            print(color.pink('No from db provided nothing to compare, try commit first?'))
            cmd(['touch', pg_sql_file])
            return

        if pg_create_from_db:
            print('Checking source db '+pg_from_db+'@'+pg_from_env+'...')
            try:
                subprocess.call(['psql',f'postgresql://{pg_from_username}:{pg_from_password}@{pg_from_hostname}:{pg_from_port}/', 
                    '-c', f'CREATE DATABASE {pg_from_db}'],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except:
                pass 

        try:
            cmd(['pgquarrel',
                '--file', pg_sql_file,
                # source db
                '--source-dbname', f'hostaddr={pg_from_hostname} port={pg_from_port} dbname={pg_from_db} user={pg_from_username} password={pg_from_password}',
                # target db
                '--target-dbname', f'hostaddr={pg_to_hostname} port={pg_to_port} dbname={pg_to_db} user={pg_to_username} password={pg_to_password}',
                # common settings
                '--table-partition', 'false',
                '--single-transaction', 'true',
                '--extension', 'true',
                '--function', 'true',
                '--procedure', 'true',
                '--exclude-schema', '^(php_test|ci_test|promo)$',
            ])

            print(color.cyan(cmd(['cat', pg_sql_file])))
            print(color.green(pg_sql_file))

            if pg_apply:
                print(color.green('Executing sql file...'))
                cmd(['psql',f'postgresql://{pg_to_username}:{pg_to_password}@{pg_to_hostname}:{pg_to_port}/{pg_to_db}', 
                    '--set', 'ON_ERROR_STOP=on',
                    '-f', pg_sql_file])

        except Exception as e:
            print(color.red('Diff file generation failed, aborting...'))
            if os.path.exists(pg_sql_file):
                cmd(['rm', pg_sql_file])
            sys.exit(1)

def pg_apply(pg_to_env, pg_to_db, pg_sql_file, pg_create_to_db=False):
    pg_to_hostname, pg_to_port, pg_to_password, pg_to_username, pg_to_db = pg_env(pg_to_env, pg_to_db)

    print(color.cyan('To db: '), color.yellow(pg_to_db)+color.green('@'+pg_to_env))
    print(color.cyan('Sql file is '+pg_sql_file))

    if pg_create_to_db:
        print('Checking target db '+pg_to_db+'@'+pg_to_env+'...')
        try:
            subprocess.call(['psql',f'postgresql://{pg_to_username}:{pg_to_password}@{pg_to_hostname}:{pg_to_port}/', 
                '-c', f'CREATE DATABASE {pg_to_db}'])
        except:
            pass
    
    print(color.green('Executing sql file...'))
    cmd(['psql',f'postgresql://{pg_to_username}:{pg_to_password}@{pg_to_hostname}:{pg_to_port}/{pg_to_db}', 
        '--set', 'ON_ERROR_STOP=on',
        '-f', pg_sql_file])

def diff_file_path(name, exit_if_absent=False, local=False):
    commit_hash = get_commit_hash()
    print(color.cyan('Commit hash:'), color.yellow(commit_hash))

    sql_diff_path = None
    if local:
        sql_diff_path = os.path.join(cmd(['pwd']), '.data')
    else:
        sql_diff_path = os.path.join(cmd(['pwd']), '.git', 'sql')
    if not exit_if_absent and not os.path.exists(sql_diff_path):
        cmd(['mkdir', sql_diff_path])

    path = os.path.join(sql_diff_path, commit_hash+'.'+name+'.sql')

    # if local:
    #     cmd(['touch', path])

    if exit_if_absent and not os.path.exists(sql_diff_path):
        print(color.red('Diff file not found'))
        sys.exit(1)

    return path


def get_exec_data(name, debug=True):
    print(color.pink('=============='+name.upper() +'==============='))
    print(color.yellow(str(sys.argv)))
    input = get_stdin_input()
    print(color.yellow(str(input)))
    command = cmd(['ps', '-o', 'args='+str(os.getppid())])
    print(command)
    command = command.splitlines()
    return (command, input)
