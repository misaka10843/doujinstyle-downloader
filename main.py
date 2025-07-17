import logging
import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import os
from urllib.parse import urljoin
from rich.logging import RichHandler

from utils.config import HEADERS, PROXY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)


def get_download_url(id):
    """通过POST请求获取重定向后的实际下载URL"""
    form_data = {
        'type': 1,
        'id': id,
        'source': 0,
        'download_link': ''
    }
    headers = HEADERS.copy()  # 创建副本避免修改原始HEADERS
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    try:
        # 发送POST请求但不跟随重定向
        response = requests.post(
            "https://doujinstyle.com/",
            data=form_data,
            allow_redirects=False,
            timeout=20,
            proxies=PROXY,
            headers=headers,
        )
        # 检查重定向头
        if 300 <= response.status_code < 400:
            location = response.headers.get('Location')
            if location:
                # 处理相对路径的重定向
                return urljoin(response.url, location)
        raise ValueError(f"服务器返回了意外状态码: {response.status_code}")

    except Exception as e:
        logger.error(f"获取下载URL出错 (ID {id}): {e}")

    return ''


def scrape_page(id):
    """处理单个ID的页面抓取任务"""
    base_url = 'https://doujinstyle.com/?p=page&type=1&id={}'
    url = base_url.format(id)
    logger.info(f"处理 ID {id}")

    try:
        # 获取页面内容
        response = requests.get(url, headers=HEADERS, timeout=30, proxies=PROXY)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 解析标题
        title = soup.select_one('mainbar h2')
        title_text = title.get_text(strip=True) if title else ''

        # 解析封面图
        cover_img = soup.select_one('#imgClick a')
        cover_url = f"https://doujinstyle.com/{cover_img['href'][2:]}" if cover_img and 'href' in cover_img.attrs else ''

        # 解析艺术家和标签
        artist, tags = '', ''
        page_wrap = soup.find('div', class_='pageWrap')
        if page_wrap:
            artist_span = page_wrap.find('span', string='Artist')
            if artist_span:
                artist_span = artist_span.find_next('span', class_='pageSpan2')
                artist = ' | '.join(a.get_text(strip=True) for a in artist_span.find_all('a')) if artist_span else ''

            tags_span = page_wrap.find('span', string='Tags:')
            if tags_span:
                tags_span = tags_span.find_next('span', class_='pageSpan2')
                tags = ' | '.join(a.get_text(strip=True) for a in tags_span.find_all('a')) if tags_span else ''
        logger.info(f"{id} 相关信息提取完成，开始获取下载链接")
        # 解析下载URL
        download_url = get_download_url(id)

        # 返回所有抓取到的数据
        return {
            'id': id,
            'title': title_text,
            'cover_url': cover_url,
            'artist': artist,
            'tags': tags,
            'download_url': download_url
        }

    except requests.RequestException as e:
        logger.error(f"网络错误 (ID {id}): {str(e)}")
    except Exception as e:
        logger.error(f"处理错误 (ID {id}): {str(e)}")

    return None


def scrape_doujinstyle():
    # ID列表文件
    ids_file = 'ids.txt'
    # 输出文件
    output_file = 'doujin_data.csv'

    if not os.path.exists(ids_file):
        logger.error(f"错误: ID文件不存在 - {ids_file}")
        return

    with open(ids_file, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]

    if not ids:
        logger.error("错误: ID文件为空")
        return

    # 准备重试列表
    failed_ids = []
    success_count = 0
    total_ids = len(ids)

    # 打开文件只写入一次
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Title', 'Cover URL', 'Artist', 'Tags', 'Download URL'])

        # 第一轮处理：尝试获取所有ID的数据
        for i, id in enumerate(ids):
            # 随机延迟防止被封
            delay = random.uniform(1.0, 3.0)
            logger.debug(f"等待 {delay:.2f} 秒...")
            time.sleep(delay)

            logger.info(f"正在处理 ({i + 1}/{total_ids}): ID {id}")
            result = scrape_page(id)

            if result and result['download_url']:
                # 写入CSV
                writer.writerow([
                    result['id'],
                    result['title'],
                    result['cover_url'],
                    result['artist'],
                    result['tags'],
                    result['download_url']
                ])
                success_count += 1
                logger.info(f"成功抓取数据")
            else:
                logger.warning(f"暂时失败，加入重试列表: ID {id}")
                failed_ids.append(id)

        # 重试处理：对失败的ID再次尝试
        if failed_ids:
            retry_count = len(failed_ids)
            logger.warning(f"第一轮有 {retry_count} 个项目失败，开始重试...")

            for i, id in enumerate(failed_ids):
                # 重试时使用较长的延迟
                delay = random.uniform(3.0, 6.0)
                logger.debug(f"重试等待 {delay:.2f} 秒...")
                time.sleep(delay)

                logger.info(f"重试处理 ({i + 1}/{retry_count}): ID {id}")
                result = scrape_page(id)

                if result:
                    # 写入CSV
                    writer.writerow([
                        result['id'],
                        result['title'],
                        result['cover_url'],
                        result['artist'],
                        result['tags'],
                        result['download_url']
                    ])
                    success_count += 1
                    logger.info(f"重试成功")
                else:
                    logger.error(f"重试后仍失败: ID {id}")

    # 最终统计报告
    failed_count = total_ids - success_count
    logger.info(f"完成! 结果已保存至: {output_file}")
    logger.info(f"总计项目: {total_ids}, 成功: {success_count}, 失败: {failed_count}")

    # 如果有失败的ID，保存到文件中
    if failed_count > 0:
        failed_file = 'failed_ids.txt'
        with open(failed_file, 'w') as f:
            for id in failed_ids:
                f.write(f"{id}\n")
        logger.warning(f"失败ID已保存到: {failed_file}")


if __name__ == '__main__':
    scrape_doujinstyle()