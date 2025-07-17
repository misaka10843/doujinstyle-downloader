import csv
import base64
import logging
import time

import requests
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from rich.logging import RichHandler

from utils.config import HEADERS, PROXY, ARIA2_TOKEN, DOWNLOAD_DIR, ARIA2_RPC, DOUJIN_CSV, DOWNLOADED_CSV
import cloudscraper

scraper = cloudscraper.create_scraper()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)


def is_mediafire_url(url):
    """检查URL是否为MediaFire链接"""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return "mediafire.com" in parsed.netloc
    except:
        return False


def get_mediafire_download_url(page_url):
    """从MediaFire页面获取实际下载URL"""
    try:
        # 获取MediaFire页面内容
        response = scraper.get(page_url, headers=HEADERS, timeout=30, proxies=PROXY)
        response.raise_for_status()

        # 解析页面内容
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找下载按钮
        download_button = soup.find("a", id="downloadButton")
        if not download_button:
            # 尝试替代选择器
            download_button = soup.find("div", class_="download-btn-container") or \
                              soup.find("div", class_="download_link")

        if download_button:
            # 获取data-scrambled-url属性
            scrambled_url = download_button.get("data-scrambled-url")
            if scrambled_url:
                # 解析base64编码的URL
                decoded_url = base64.b64decode(scrambled_url).decode("utf-8")
                logger.info(f"已解码MediaFire下载URL: {decoded_url}")
                return decoded_url

        # 尝试直接获取直接下载链接
        direct_link = soup.find("a", href=True, id="direct_download")
        if direct_link:
            logger.info("找到直接下载链接")
            return direct_link["href"]

        # 尝试从页面脚本中提取下载URL
        for script in soup.find_all("script"):
            if "window.location" in script.text:
                start = script.text.find("window.location") + len("window.location")
                end = script.text.find(";", start)
                if start > -1 and end > -1:
                    url_line = script.text[start:end].strip()
                    logger.info(f"从脚本中找到跳转: {url_line}")
                    return url_line.split('=')[1].strip("'\"")

        logger.warning(f"未能在页面中找到下载链接: {page_url}")
        return None

    except scraper.RequestException as e:
        logger.error(f"请求MediaFire页面失败: {page_url} - {str(e)}")
    except Exception as e:
        logger.error(f"解析MediaFire页面失败: {str(e)}")

    return None


def send_to_aria2(download_url, filename=None):
    """通过RPC发送下载任务到aria2"""
    if not download_url:
        logger.error("下载URL为空，无法发送到aria2")
        return False

    try:
        payload = {
            "jsonrpc": "2.0",
            "id": "qwer",
            "method": "aria2.addUri",
            "params": [
                f"token:{ARIA2_TOKEN}",
                [download_url],
                {
                    "dir": DOWNLOAD_DIR,
                }
            ]
        }

        # 如果提供了文件名，添加到参数
        if filename:
            payload["params"][2]["out"] = filename

        response = requests.post(
            ARIA2_RPC,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        # 检查响应
        result = response.json()
        if "result" in result:
            logger.info(f"下载任务已添加到aria2: {result['result']}")
            return result["result"]
        else:
            logger.error(f"aria2返回错误: {result.get('error', '未知错误')}")
            return False

    except requests.RequestException as e:
        logger.error(f"连接aria2 RPC失败: {str(e)}")
    except Exception as e:
        logger.error(f"发送到aria2失败: {str(e)}")

    return False


def process_csv(input_file, output_file):
    """处理CSV文件并下载MediaFire链接"""
    processed = 0
    success = 0

    if not os.path.exists(input_file):
        logger.error(f"输入CSV文件不存在: {input_file}")
        return

    # 读取CSV文件
    with open(input_file, "r", newline="", encoding="utf-8") as infile, \
            open(output_file, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        # 添加额外状态列
        fieldnames = reader.fieldnames + ["MediaFire", "Download_URL", "GID", "Status"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            processed += 1
            download_url = row["Download URL"]

            # 添加处理状态字段
            row["MediaFire"] = "No"
            row["Download_URL"] = ""
            row["GID"] = ""
            row["Status"] = "Skipped"

            try:
                # 检查是否是MediaFire链接
                if is_mediafire_url(download_url):
                    logger.info(f"处理MediaFire链接 [{processed}]: {download_url}")
                    row["MediaFire"] = "Yes"

                    # 获取真实下载URL
                    actual_url = get_mediafire_download_url(download_url)

                    if actual_url:
                        row["Download_URL"] = actual_url

                        # 发送到aria2
                        # 使用ID作为文件名的一部分，避免特殊字符问题
                        safe_title = "".join(c for c in row["Title"] if c.isalnum())[:50]
                        filename = f"{row['ID']}_{safe_title}.zip" if row["Title"] else None

                        gid = send_to_aria2(actual_url, filename)

                        if gid:
                            row["GID"] = gid
                            row["Status"] = "Queued"
                            success += 1
                        else:
                            row["Status"] = "Aria2_Error"
                    else:
                        row["Status"] = "URL_Extraction_Failed"
                else:
                    logger.info(f"跳过非MediaFire链接 [{processed}]: {download_url}")

            except Exception as e:
                logger.error(f"处理记录失败: {row['ID']} - {str(e)}")
                row["Status"] = f"Error: {str(e)[:50]}"

            # 写入结果
            writer.writerow(row)
            time.sleep(3)

    logger.info(f"处理完成! 总数: {processed}, 成功添加到aria2: {success}")


if __name__ == "__main__":
    logger.info("===== MediaFire下载处理程序启动 =====")
    # 处理CSV文件
    process_csv(DOUJIN_CSV, DOWNLOADED_CSV)

    logger.info("===== 处理完成 =====")
