import re
import os

HTML_PATH = r'V:\Default\Desktop\当前学习内容\寻找导师的邮件\李自翔\量子蒙特卡洛\pilot-test\output\中科院物理所\超快物质科学中心\张鹏举\pengju_homepage.html'

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()

print('=== Keywords found ===')
for kw in ['张鹏举', 'Pengju', 'pengju', 'iphy.ac.cn', '研究员', '教授', '研究方向', '邮箱', 'email', '教育', '简历', '阿秒', '强场', '超快', '激光', '中科院', '物理所', '高次谐波', 'HHG', '成像', '衍射', '晶体', '博士', '光学']:
    matches = list(re.finditer(re.escape(kw), text))
    if matches:
        for m in matches[:2]:
            i = m.start()
            ctx = text[max(0,i-100):i+300]
            ctx_clean = re.sub(r'\s+', ' ', ctx)
            print(f'\n[{kw}] ({len(matches)} matches total)')
            print('...', ctx_clean[:300], '...')
