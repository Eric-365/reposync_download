import os
import subprocess
import sys
import shutil
from pathlib import Path
from tqdm import tqdm
import threading
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# 获取仓库id和架构
def repo_id_arch():
    repolist_output = subprocess.run(
        ["dnf", "repolist"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ).stdout

    repo_ids = {}
    for line in repolist_output.splitlines()[1:]:
        repo_id = line.split()[0]
        repo_ids[repo_id] = []

        repoquery_output = subprocess.run(
            ["dnf", "repoquery", "--repo", repo_id, "--qf", "%{arch}", "--all"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ).stdout
        # Fix: Use splitlines() instead of splitlines()[1:]
        for arch in repoquery_output.splitlines():
            repo_ids[repo_id].append(arch)

    print("    获取到的仓库id和架构信息：")
    for repo_id, arches in repo_ids.items():
        print(f"仓库id: {repo_id}, 架构: {', '.join(arches)}")
           
    return repo_ids

def update_version(name):
    file_path = "/etc/os-version"
    # Read the file content
    with open(file_path, "r") as file:
        lines = file.readlines()

        # Update the necessary lines
    with open(file_path, "w") as file:
        for line in lines:
            if line.startswith("EditionName="):
                file.write(f"EditionName={name}\n")
            elif line.startswith("EditionName[zh_CN]="):
                file.write(f"EditionName[zh_CN]={name}\n")
            else:
                file.write(line)
    print(f"更新version版本为 '{name}' 版")

def reposync_update(repo_id, arch, rpm_path):
    rpm_path = Path(rpm_path)
    repo_id = Path(repo_id)
    repo_dir = rpm_path / repo_id
    if not repo_dir.exists():
        os.makedirs(repo_dir)

    # 设置日志文件路径
    log_file = '/var/log/reposync_download/reposync_update.log'

    # 创建Popen进程以实时获取输出
    process = subprocess.Popen(
        ["dnf", "reposync", "--repoid", repo_id, "--download-path", str(repo_dir), "--arch", arch, "--norepopath", "--newest-only"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    for line in process.stdout:
        # 写入日志文件
        with open(log_file, 'a') as log:
                if "[SKIPPED]" not in line:  # 过滤掉包含 [SKIPPED] 的行
                    log.write(line.strip() + "\n")

    process.stdout.close()
    process.stderr.close()
    process.wait()

# 定义函数来读取配置文件
def read_email_config(config_path):
    config = {}
    try:
        with open(config_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return None
    return config

# 定义邮件发送函数
def send_email_with_log():
    config_path = '/usr/local/reposync_download/email.conf'
    log_file_path = '/var/log/reposync_download/reposync_update.log'

    # 读取配置文件
    config = read_email_config(config_path)

    if not config:
        print("无法加载配置文件，退出函数。")
        return

    # 验证必要字段是否存在
    required_fields = ["sender_email", "password", "smtp_server", "smtp_port", "sender_subject", "receiver_email"]
    for field in required_fields:
        if field not in config or not config[field]:
            print(f"缺少必要字段 {field}，无法发送邮件")
            return

    # 加载日志文件内容作为邮件正文
    try:
        with open(log_file_path, 'r') as log_file:
            email_body = log_file.read()
    except Exception as e:
        print(f"无法读取日志文件: {e}")
        return

    # 设置邮件内容
    msg = MIMEMultipart()
    msg['From'] = config['sender_email']
    msg['To'] = config['receiver_email']
    msg['Subject'] = config['sender_subject']
    msg.attach(MIMEText(email_body, 'plain'))

    # 发送邮件
    try:
        server = smtplib.SMTP_SSL(config['smtp_server'], int(config['smtp_port']))
        server.login(config['sender_email'], config['password'])
        server.sendmail(config['sender_email'], config['receiver_email'], msg.as_string())
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败：{e}")
    finally:
        if 'server' in locals():
            server.quit()

def timer_main():

    # 检查是否通过命令行参数传入
    if len(sys.argv) > 1:
        need_schedule = sys.argv[1].strip().lower()
    else:
        need_schedule = input("  是否需要设定定时任务，输入Y/N: ").strip().lower()

    if need_schedule == 'y':
        # 选择每周或每月
        period = input("  是每周还是每月执行定时任务，请输入mouth或week：").strip().lower()

        if period == 'mouth':
            # 输入每月几号执行
            try:
                day = int(input("  是每月几号执行定时任务，输入数字是1-28："))
                if day < 1 or day > 28:
                    print("  输入无效，结束脚本")
                    sys.exit()
            except ValueError:
                print("  输入无效，结束脚本")
                sys.exit()

            # 输入每天几点执行
            try:
                hour = int(input("  是每天几点执行定时任务，输入数字是0-23："))
                if hour < 0 or hour > 23:
                    print("  输入无效，结束脚本")
                    sys.exit()
            except ValueError:
                print("  输入无效，结束脚本")
                sys.exit()

            # 使用crontab设定执行任务
            crontab_command = f"echo '{hour} {day} * * * /usr/local/reposync_download/reposync_timer n' | crontab -"
            os.system(crontab_command)
            print(f"  定时任务已设定：每月{day}日{hour}点执行reposync_timer任务")
            sys.exit()

        elif period == 'week':
            # 输入每周几号执行
            try:
                week_day = int(input("  是每周几号执行定时任务，输入数字是1-7："))
                if week_day < 1 or week_day > 7:
                    print("  输入无效，结束脚本")
                    sys.exit()
            except ValueError:
                print("  输入无效，结束脚本")
                sys.exit()

            # 输入每天几点执行
            try:
                hour = int(input("  是每天几点执行定时任务，输入数字是0-23："))
                if hour < 0 or hour > 23:
                    print("  输入无效，结束脚本")
                    sys.exit()
            except ValueError:
                print("  输入无效，结束脚本")
                sys.exit()

            # 使用crontab设定执行任务
            crontab_command = f"echo '{hour} * * * {week_day} /usr/local/reposync_download/reposync_timer n' | crontab -"
            os.system(crontab_command)
            print(f"  定时任务已设定：每周周{week_day}的{hour}点执行reposync_timer任务")
            sys.exit()

        else:
            print("  输入无效，结束脚本")
            sys.exit()

    elif need_schedule == 'n':
        print("  不设定定时任务，执行一次仓库更新任务，通过tail -f /var/log/reposync_download/reposync_update.log")
    else:
        print("  输入无效，结束脚本")
        sys.exit()

    backup_dir = '/var/log/reposync_download/log_bak/'
    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        os.makedirs(backup_dir)

    # 备份日志文件
    log_file = '/var/log/reposync_download/reposync_update.log'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = Path(backup_dir) / f"{timestamp}_reposync_update.log"
    if os.path.exists(log_file):
        os.rename(log_file, backup_file)  # 将日志文件移动到备份目录并重命名

    # 清空日志文件
    open(log_file, 'w').close()

    # 文件路径
    file_path = "/var/log/reposync_download/task_info.txt"

    # 读取文件内容
    with open(file_path, "r") as file:
        line = file.readline().strip()  # 读取第一行并去除两端空格和换行符

    # 使用空格分隔内容并赋值
    choice, rpm_path = line.split(" ", 1)

    ####调用函数repo_ids = repo_id_arch()
    ####判断变量，执行1,2,3种不同的任务
    if choice == '1':
        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-a.repo', '/etc/yum.repos.d/')
        update_version("a")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()
        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_update(repo_id, arch, rpm_path)
            # 使用createrepo创建元数据
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", "--update", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    elif choice == '2':
        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-e.repo', '/etc/yum.repos.d/')
        update_version("e")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_update(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", "--update", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    
    elif choice == '3':
        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-a.repo', '/etc/yum.repos.d/')
        update_version("a")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_update(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", "--update", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-e.repo', '/etc/yum.repos.d/')
        update_version("e")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_update(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", "--update", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    timer_main()
    send_email_with_log()