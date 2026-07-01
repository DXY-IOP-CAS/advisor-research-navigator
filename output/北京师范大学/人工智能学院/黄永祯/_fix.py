#!/usr/bin/env python3
"""Fix all verify_profile issues."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

P = "output/北京师范大学/人工智能学院/黄永祯/01_基础画像.md"
A = "output/北京师范大学/人工智能学院/黄永祯/archive/20260702_032113/01_基础画像_draft.md"

with open(P, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace the entire CV section
old = "## 2. 学术履历\n\n| 时间 | 机构 | 职位 | 方向 |\n| 2002–2006 | 华中科技大学人工智能与自动化学院 | 学士 | 自动化 |\n| 2006–2011 | 中国科学院自动化研究所 | 博士（师从谭铁牛院士） | 模式识别与智能系统 |\n| 2011–2013 | 中国科学院自动化研究所 | 助理研究员 | 计算机视觉、模式识别 |\n| 2013–2021 | 中国科学院自动化研究所 | 副研究员 | 计算机视觉、模式识别 |\n| 2021–2022 | 北京师范大学人工智能学院 | 研究员 | 计算机视觉、模式识别 |\n| 2022–至今 | 北京师范大学人工智能学院 | 教授 | 计算机视觉、多模态感知 |\n\n\n---\n"

new = "## 2. 学术履历\n\n| 时间 | 机构 | 职位 | 方向 |\n|:-----|:-----|:-----|:-----|\n| 2002–2006 | 华中科技大学人工智能与自动化学院 | 学士 | 自动化 |\n| 2006–2011 | 中国科学院自动化研究所 | 博士（师从谭铁牛院士） | 模式识别与智能系统 |\n| 2011–2013 | 中国科学院自动化研究所 | 助理研究员 | 计算机视觉、模式识别 |\n| 2013–2021 | 中国科学院自动化研究所 | 副研究员 | 计算机视觉、模式识别 |\n| 2021–2022 | 北京师范大学人工智能学院 | 研究员 | 计算机视觉、模式识别 |\n| 2022–至今 | 北京师范大学人工智能学院 | 教授 | 计算机视觉、多模态感知 |\n\n---\n"

if old in content:
    content = content.replace(old, new)
    print("CV section FIXED")
else:
    print("CV pattern NOT FOUND - checking alternate patterns")
    # Try with en-dash
    if '–' in content:
        print("en-dash found")
    if '—' in content:
        print("em-dash found")

# Fix 2: Remove duplicate HID paper
count = 0
new_lines = []
for l in content.split('\n'):
    if 'Human Identification at a Distance' in l:
        count += 1
        if count > 1:
            continue
    new_lines.append(l)
content = '\n'.join(new_lines)

# Fix 3: Also check 验证来源 section number
# If section 9 (验证来源) and 8 (数据质量) both exist, renumber 9->8
if '## 8. 数据质量说明' in content and '## 9. 数据质量说明' not in content and '## 7. 验证来源' in content:
    # Check if data quality is after 验证来源 (section 7)
    idx7 = content.find('## 7. 验证来源')
    idx8 = content.find('## 8. 数据质量说明')
    if idx8 > idx7:
        # data quality should be section 9
        content = content.replace('## 8. 数据质量说明', '## 9. 数据质量说明')
        print("Data quality renumbered to 9")
    else:
        content = content.replace('## 7. 验证来源', '## 7. 数据质量说明')
        print("Data quality renumbered to 7")

# Write back
with open(P, 'w', encoding='utf-8') as f:
    f.write(content)
with open(A, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done, " + str(len(content)) + " chars")
