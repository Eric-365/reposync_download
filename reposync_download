import os
import subprocess
import sys
import shutil
from pathlib import Path
from tqdm import tqdm
import threading
import re

# 检查环境函数 new
def check_info():
    if os.geteuid() != 0:
        print("    需要在root环境执行")
        sys.exit(1)
    if not (Path('./uos-e.repo').exists() and Path('./uos-a.repo').exists()):
        print(".repo不存在，请放置.repo文件")
        sys.exit(1)
    # 获取 dnf 版本
    try:
        output = subprocess.check_output(["dnf", "--version"], text=True).splitlines()
        version = output[0].strip()  # 获取第一行的版本号
    # 比较版本号
        if tuple(map(int, version.split("."))) < (4, 7, 0):
            print("    请升级dnf版本，请使用dnf update dnf dnf-plugins-core进行更新")
            sys.exit(1)
    except FileNotFoundError:
        print("    dnf 未安装，请先安装 dnf")
        sys.exit(1)
    except Exception as e:
        print(f"    发生错误: {e}")
        sys.exit(1)
    try:
        subprocess.run(["createrepo", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("    缺少createrepo命令行，请使用yum  install  createrepo")
        sys.exit(1)
    if not Path('/var/log/reposync_download').exists():
        os.makedirs('/var/log/reposync_download')
    yum_repo_dir = Path("/etc/yum.repos.d/")
    for repo_file in yum_repo_dir.glob("*"):
        os.remove(repo_file)
    if not Path('/etc/yum.repos.d/').exists():
        os.makedirs('/etc/yum.repos.d/')
    print("*******************************************\n*           环境检查成功，执行下一步      *\n*******************************************")


# 选择函数
def choice_info():
    print("  请问下载哪个路线的全量仓库，请选择序号：")
    print("  1.只下载a版路线的全量仓库")
    print("  2.只下载e版路线的全量仓库")
    print("  3.同时下载a和e版路线的全量仓库")
    choice = input("    请输入需要选择的数字：")
    if choice not in ['1', '2', '3']:
        print("无效输入")
        sys.exit(1)
    rpm_path = input("    请问下载的rpm存储在哪个目录下\n    (请输入绝对路径，例如：/data/repo/): ")
    rpm_path = Path(rpm_path)
    if not rpm_path.exists():
        os.makedirs(rpm_path)
    total, used, free = shutil.disk_usage(rpm_path)
    if free < 100 * 1024 * 1024 * 1024:
        print("    存储空间不足100G")
        sys.exit(1)
    return choice, rpm_path


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


# 日志记录
def log_output(logfile, msg):
    with open(logfile, 'a') as log:
        log.write(msg + "\n")

def reposync_createrepo(repo_id, arch, rpm_path):
    repo_dir = rpm_path / repo_id
    if not repo_dir.exists():
        os.makedirs(repo_dir)
    # 设置日志文件路径
    log_file = '/var/log/reposync_download/reposync.log'
    # 创建Popen进程以实时获取输出
    process = subprocess.Popen(
        ["dnf", "reposync", "--repoid", repo_id, "--download-path", str(repo_dir), "--arch", arch, "--norepopath"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    # 初始化进度条
    progress_bar = tqdm(
        total=None,  # 初始总数未知
        unit="files",  # 单位为文件数
        desc=f"Downloading {repo_id}-{arch}",
        dynamic_ncols=True
    )
    # 使用正则表达式匹配下载状态
    pattern = re.compile(r"(\d+)\s*/\s*(\d+)")  # 匹配 "已下载数量/总数" 格式
    for line in process.stdout:
        # 写入日志文件
        with open(log_file, 'a') as log:
            log.write(line.strip() + "\n")
        # 查找进度信息
        match = pattern.search(line)
        if match:
            downloaded = int(match.group(1))  # 已下载数量
            total = int(match.group(2))      # 总数
            # 更新进度条总数
            if progress_bar.total is None or progress_bar.total != total:
                progress_bar.total = total
                progress_bar.refresh()
            # 更新已下载数量
            progress_bar.n = downloaded
            progress_bar.last_print_n = downloaded
            progress_bar.update(0)  # 强制刷新进度条
    process.stdout.close()
    process.stderr.close()
    process.wait()

    progress_bar.close()


# 主程序执行
def main():
    check_info()
    choice, rpm_path = choice_info()

    if choice == '1':
        with open('/var/log/reposync_download/task_info.txt', 'w') as f:
            f.write("1"+" "+f"{rpm_path}")
            
        task_input = input("  1.如果需要后台执行下载任务，请输入1 \n  2.如果需要前端执行下载任务，请输入2 \n    请输入需要选择的任务类型:").strip()
        if task_input not in ['1', '2']:
            print("输入信息错误，将中止脚本，重新输入正确的选择")
            sys.exit(1)
        if task_input in ['1']:
            print("在后台执行同步仓库的任务，可通过tail -f /var/log/reposync_download/reposync.log查看详细下载日志;\n通过tail -f ./nohup.out查看基础运行日志")
            os.system(f"nohup /usr/local/reposync_download/reposync_task &")
            sys.exit(1)
        else:
            print("将继续执行下载任务，可通过tail -f /var/log/reposync_download/reposync.log查看下载日志")

        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-a.repo', '/etc/yum.repos.d/')
        update_version("a")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_createrepo(repo_id, arch, rpm_path)
            # 使用createrepo创建元数据
            print(f"正在创建元数据 {repo_id} ...")
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    elif choice == '2':
        with open('/var/log/reposync_download/task_info.txt', 'w') as f:
            f.write("2"+" "+f"{rpm_path}")

        task_input = input("  1.如果需要后台执行下载任务，请输入1 \n  2.如果需要前端执行下载任务，请输入2 \n    请输入需要选择的任务类型:").strip()
        if task_input not in ['1', '2']:
            print("输入信息错误，将中止脚本，重新输入正确的选择")
            sys.exit(1)
        if task_input in ['1']:
            print("在后台执行同步仓库的任务，可通过tail -f /var/log/reposync_download/reposync.log查看详细下载日志;\n通过tail -f ./nohup.out查看基础运行日志")
            os.system(f"nohup /usr/local/reposync_download/reposync_task &")
            sys.exit(1)
        else:
            print("将继续执行下载任务，可通过tail -f /var/log/reposync_download/reposync.log查看下载日志")

        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-e.repo', '/etc/yum.repos.d/')
        update_version("e")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_createrepo(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    
    elif choice == '3':
        with open('/var/log/reposync_download/task_info.txt', 'w') as f:
            f.write("3"+" "+f"{rpm_path}")

        task_input = input("  1.如果需要后台执行下载任务，请输入1 \n  2.如果需要前端执行下载任务，请输入2 \n    请输入需要选择的任务类型:").strip()
        if task_input not in ['1', '2']:
            print("输入信息错误，将中止脚本，重新输入正确的选择")
            sys.exit(1)
        if task_input in ['1']:
            print("将在后台执行同步仓库的任务，可通过tail -f /var/log/reposync_download/reposync.log查看详细下载日志;\n通过tail -f ./nohup.out查看基础运行日志")
            os.system(f"nohup /usr/local/reposync_download/reposync_task &")
            sys.exit(1)
        else:
            print("将继续执行下载任务，可通过tail -f /var/log/reposync_download/reposync.log查看下载日志")

        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-a.repo', '/etc/yum.repos.d/')
        update_version("a")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_createrepo(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-e.repo', '/etc/yum.repos.d/')
        update_version("e")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()

        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_createrepo(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    main()
