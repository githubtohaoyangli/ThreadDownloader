# ThreadDownloader 多线程下载器

## English 英语

Thread downloader,let the downloading faster.  
I only developed CLI program.  
If you want,you can build the source code by Cython,Pyinstaller or others.  
I downloaded a ISO file with this.I just use **64 threads**,and it takes just **10 minutes**.
This Program only works on Windows.I will try to let it can use on Linux and Mac.

## Chinese Simpled 简体中文

多线程下载器，让下载更快。  
我只开发了命令行版本。
我使用这个下载了一个ISO文件，只是开了**64个**线程，只花了**10分钟**。  
这个程序只能在Windows上使用，我会试着让它可以在Linux和Mac上运行的。

### 用法

1、下载[PyPy3.10](https://downloads.python.org/pypy/pypy3.10-v7.3.15-win64.zip)，把它解压到一个目录下。
2、按下Ctrl+X，点击“系统(Y)
”，在页面上找到“高级系统设置”，点击“环境变量”。如果解压在用户目录下，需要在“XXX的用户变量”中操作；否则在“系统变量”中操作。新建一项，内容：<
解压后的PyPy目录>。  
3、下载<https://github.com/littlepiggeon/ThreadDownloader/archive/refs/heads/Windows.zip>，解压。  
4、按下Win+R，输入cmd或powershell，输入“pypy <解压目录下downloader.pyd的路径> -u <链接> -d <文件下载到的目录>”即开始下载。