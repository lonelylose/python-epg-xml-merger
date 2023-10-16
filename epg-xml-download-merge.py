import schedule
import time
import requests
import os
import glob
import gzip
import shutil
from lxml import etree

# 设置时区为UTC+8，即东八区
os.environ['TZ'] = 'Asia/Shanghai'
# 应用时区设置
time.tzset()

# 获取当前日期，格式为2023-10-16
date = time.strftime("%Y-%m-%d")
# 拼接文件名，格式为2023-10-16-pp.xml
filename = date + "-pp.xml"
# 下载xml文件，并保存到本地
url = "https://epg.112114.xyz/pp.xml"

# 定义一个函数来下载和合并xml文件，并复制到/var/www/html/目录下，并压缩成gz文件
def download_and_merge_xml():
    # 定义一个变量来表示保留天数，可以根据需要修改
    keep_days = 7

    # 获取当前时间戳（以秒为单位）
    now = time.time()

    # 遍历当前目录下所有以.xml结尾的文件名
    for xml_file in glob.glob("*.xml"):
        # 获取文件的修改时间戳（以秒为单位）
        mtime = os.path.getmtime(xml_file)
        # 如果文件修改时间距离当前时间超过了保留天数（以秒为单位），就删除文件
        if now - mtime > keep_days * 24 * 60 * 60:
            os.remove(xml_file)
            # 打印提示信息
            print(f"Deleted {xml_file}")

    response = requests.get(url)
    # 打开文件为写入模式，并指定编码为utf-8
    with open(filename, "w", encoding="utf-8") as f:
        # 将响应内容解码为utf-8字符串，并写入文件中
        f.write(response.content.decode("utf-8"))
    # 打印提示信息
    print(f"Downloaded {filename}")

    # 获取当前目录下所有以.xml结尾的文件名，并排除掉7D.xml
    xml_files = [f for f in glob.glob("*.xml") if f != "7D.xml"]


    # 创建一个空的xml树对象
    merged_tree = None

    # 遍历每个xml文件，并将其内容合并到一个树中
    for xml_file in xml_files:
        # 打开xml文件为只读模式，并指定编码为utf-8
        with open(xml_file, "r", encoding="utf-8") as f:
            # 解析xml文件为一个xml树对象
            tree = etree.parse(f)
        # 如果合并的树为空，就用第一个树作为基础
        if merged_tree is None:
            merged_tree = tree.getroot()
        else:
            # 否则，就用extend()方法来合并两个树的子元素
            merged_tree.extend(tree.getroot())

    # 使用tostring()方法来生成xml文件的字符串表示，并指定编码为utf-8和美化输出
    xml_str = etree.tostring(merged_tree, encoding="utf-8", pretty_print=True).decode("utf-8")
    # 在字符串的开头加上想要的声明
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    
    # 打开文件为写入模式，并指定编码为utf-8
    with open("7D.xml", "w", encoding="utf-8") as f:
        # 将字符串写入到文件中
        f.write(xml_str)
    
    # 复制7D.xml文件到/var/www/html/目录下
    shutil.copy("7D.xml", "/var/www/html/")

    # 打印提示信息
    print(f"Copied 7D.xml to /var/www/html/")

    # 打开xml文件为只读模式，并指定编码为utf-8
    with open("7D.xml", "r", encoding="utf-8") as xml_file:
        # 打开gz文件为写入模式，并指定压缩级别为9（最高）
        with gzip.open("7D.xml.gz", "wb", compresslevel=9) as gz_file:
            # 将xml文件的内容编码为字节串，并复制到gz文件中
            gz_file.write(xml_file.read().encode("utf-8"))

    # 打印提示信息
    print(f"Compressed 7D.xml to 7D.xml.gz")

    # 复制7D.xml.gz文件到/var/www/html/目录下
    shutil.copy("7D.xml.gz", "/var/www/html/")

    # 打印提示信息
    print(f"Copied 7D.xml.gz to /var/www/html/")

# 安排每天0点和12点执行下载和合并xml文件的任务
schedule.every().day.at("00:58").do(download_and_merge_xml)
schedule.every().day.at("08:00").do(download_and_merge_xml)

# 创建一个无限循环，检查并执行安排好的任务
while True:
    schedule.run_pending()
    time.sleep(1)
