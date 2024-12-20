简介
工具概述：reposync_download是一个批量同步仓库，定时同步仓库并可以设置发送邮件的工具。
背景说明：在a/e版服务器上，实际使用 dnf reposync 和 createrepo 时，我们发现同步仓库时可能会遇到架构遗漏或下载的仓库元数据与 RPM 包不匹配的问题。为了解决这些问题，我们不断优化了 reposync_download 工具。从最初的 Shell 脚本，到 Python 脚本，再到最终的 RPM 安装包，这一系列的演变使得工具更加稳定和易用。我们希望 reposync_download 能帮助普通用户更加便捷地批量同步官方仓库，同时简化部署过程。
使用场景：对于普通用户，若其拥有一台服务器并希望搭建一个内网仓库，同时使该服务器能够连接外网同步更新安装包，并且希望每周或每月进行仓库的更新，更新完成后也会发送邮件给特定的邮箱。
安装与环境要求
前置条件：统信服务器操作系统a/e版，服务器操作系统需要联网且激活。
安装步骤：yum  install  ./reposync_download-1.0-1.uelc20.x86_64.rpm
功能与特点
安装目录：安装完成后，目录位于/usr/local/reposync_download/
文件说明：
oemail.conf：用于配置邮箱的基础信息。
ouos-a.repo：用于配置a版仓库的仓库文件。
ouos-e.repo：用于配置e版仓库的仓库文件。
oreposync_download：用于批量同步下载仓库。
oreposync_task：搭配reposync_download使用，用于后台任务执行。
oreposync_timer：用于设定定时任务批量更新仓库，邮箱通知功能。
定时同步任务：如何设定定时任务，定期同步仓库。
元数据处理：下载后的所有rpm包都使用createrepo批量创建元数据，如果是更新的rpm包，则使用createrepo --update更新元数据。
错误处理与日志：同步过程中可能出现的错误类型及其解决方案。
邮件通知功能：同步任务执行后的通知功能，且配置了邮箱的基础信息，则会发送/var/log/reposync_download/reposync_update.log日志给指定的邮箱。
多仓库支持：支持同步多个仓库的操作与配置，同时，目前安装完即可同步1050的仓库，如果需要同步1060或1070仓库，需要针对。
