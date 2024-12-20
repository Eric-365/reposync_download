import os
import subprocess
import sys
import shutil
from pathlib import Path
from tqdm import tqdm
import threading
import re


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


def reposync_task(repo_id, arch, rpm_path):
    rpm_path = Path(rpm_path)
    repo_id = Path(repo_id)
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
    
    for line in process.stdout:
        # 写入日志文件
        with open(log_file, 'a') as log:
            log.write(line.strip() + "\n")

    process.stdout.close()
    process.stderr.close()
    process.wait()

def task_main():
    ###读取文件中的两个变量
    # 文件路径
    file_path = "/var/log/reposync_download/task_info.txt"

    # 读取文件内容
    with open(file_path, "r") as file:
        line = file.readline().strip()  # 读取第一行并去除两端空格和换行符

    # 使用空格分隔内容并赋值
    choice, rpm_path = line.split(" ", 1)

    if choice == '1':
        for repo_file in Path("/etc/yum.repos.d/").glob("*"):
            os.remove(repo_file)
        shutil.copy('./uos-a.repo', '/etc/yum.repos.d/')
        update_version("a")
        os.system(f"yum clean all && yum makecache")
        repo_ids = repo_id_arch()
        for repo_id, arches in repo_ids.items():
            for arch in arches:
                reposync_task(repo_id, arch, rpm_path)
            # 使用createrepo创建元数据
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
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
                reposync_task(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
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
                reposync_task(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
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
                reposync_task(repo_id, arch, rpm_path)
            print(f"正在创建元数据 {repo_id} ...")
            rpm_path = Path(rpm_path)
            repo_id = Path(repo_id)
            repo_dir = rpm_path / repo_id
            subprocess.run(["createrepo", str(repo_dir)],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    task_main()