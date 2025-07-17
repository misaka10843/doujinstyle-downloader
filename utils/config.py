import os
from dotenv import load_dotenv

load_dotenv(verbose=True)

DOUJIN_CSV = os.getenv("DOUJIN_CSV") or 'doujin_data.csv'
DOWNLOADED_CSV = os.getenv("DOWNLOADED_CSV") or 'download_results.csv'
ARIA2_RPC = os.getenv("ARIA2_RPC") or 'http://localhost:6800/jsonrpc'
ARIA2_TOKEN = os.getenv("ARIA2_TOKEN") or ''
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR") or './doujinstyle'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "cookie":"ukey=1rzghsz29ozzmdki5v7gmnpnmu33s5g9; conv_tracking_data-2=%7B%22mf_source%22%3A%22regular_download-59%22%2C%22mf_content%22%3A%22Free%22%2C%22mf_medium%22%3A%22windows%5C%2FEdge%22%2C%22mf_campaign%22%3A%22fa7ocwnexpn497y%22%2C%22mf_term%22%3A%225486ee53984c1c24c5975673e412bcae%22%7D; __cf_bm=7nMqJ_mMUBQmAE3DdFGtwFl8WNWrAuQIIl0OSWfCA5o-1752570292-1.0.1.1-DZz30ITIXbIp6ohfqzu9zV1Ooc2gsjiZc8wRz_ks4W.Cf4DG11iuyucEQJ4UIDNAugiy5kV0g82wyaPZ210HZaBhCzVNcrP2QqCTs8KXVwI; _gid=GA1.2.162739515.1752570294; _gat_gtag_UA_829541_1=1; _ga_K68XP6D85D=GS2.1.s1752570293$o1$g0$t1752570293$j60$l0$h0; _ga=GA1.1.69847917.1752570294; cf_clearance=3hNa8VaRsjr5bpP1aARYQBtMonsmiVD18kYWU7WfOOw-1752570294-1.2.1.1-98nxKUt5ila0BKub.e968b90DKU84_KIR.yg7IYmztVDIPiXie9xdhb.moTliKXvK5mhoySDTxgrY0ssl3WoGmMb.QHBBgWqTy1rKgWsd8ZNC6ShqV2._JZmJqQyagfmhUXVj3.wzA8MaXkKwIRyRB6XoErPGv6rZtBV1Frpp9gcDaF2An1M3GWr.JTqhPwOao0pfTi5ojilxJAhaWa31k2jQF6zaisnZ40fIHho0qk; amp_28916b=FTeeFWjpqBSyYbOpXVuKxb...1j06l8rp0.1j06l8rp1.0.1.1",

}
PROXY = {
    'http': os.getenv("PROXY") or '',
    'https': os.getenv("PROXY") or '',
}
