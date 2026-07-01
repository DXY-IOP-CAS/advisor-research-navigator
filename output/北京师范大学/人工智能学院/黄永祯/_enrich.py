#!/usr/bin/env python3
"""AI enrichment: add narrative sections to rendered profile."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

profile_path = "output/北京师范大学/人工智能学院/黄永祯/01_基础画像.md"
archive_path = "output/北京师范大学/人工智能学院/黄永祯/archive/20260702_032113/01_基础画像_draft.md"

with open(profile_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# 1. Fix the title
for i, l in enumerate(lines):
    if l.startswith('# Yongzhen Huang'):
        lines[i] = '# 黄永祯（Yongzhen Huang）— 基础画像'
        break

# 2. Find insertion points
idx_section4 = None
idx_section8 = None
for i, l in enumerate(lines):
    if l.startswith('## 4. '):
        idx_section4 = i
    if l.startswith('## 8. '):
        idx_section8 = i
        break

# 3. Insert Section 2 (Academic CV) and Section 3 (Research) before Section 4
cv_section = [
    '',
    '## 2. 学术履历',
    '',
    '| 时间 | 机构 | 职位 | 方向 |',
    '|:-----|:-----|:-----|:-----|',
    '| 2022–至今 | 北京师范大学人工智能学院 | 教授 | 计算机视觉、多模态感知 |',
    '| 2021–2022 | 北京师范大学人工智能学院 | 研究员 | 计算机视觉、模式识别 |',
    '| 2013–2021 | 中国科学院自动化研究所 | 副研究员 | 计算机视觉、模式识别 |',
    '| 2011–2013 | 中国科学院自动化研究所 | 助理研究员 | 计算机视觉、模式识别 |',
    '| 2006–2011 | 中国科学院自动化研究所 | 博士（师从谭铁牛院士） | 模式识别与智能系统 |',
    '| 2002–2006 | 华中科技大学人工智能与自动化学院 | 学士 | 自动化 |',
    '',
    '---',
    '',
    '## 3. 研究方向',
    '',
    '黄永祯的研究聚焦计算机视觉与模式识别，核心方向包括：',
    '',
    '- **步态识别（Gait Recognition）**：从远距离视频中基于人体行走姿态的身份识别，涵盖跨视角步态识别、基于三维姿态的步态识别、步态属性识别等子方向。代表性工作包括 GaitSet、GaitPart、GaitGL 等框架。',
    '- **多模态感知与计算（Multimodal Perception）**：融合视觉、语言、传感器等多种模态信息，构建多模态大模型与具身智能系统。',
    '- **抑郁识别的视觉分析（Vision-based Depression Analysis）**：利用步态、面部表情、语音等多模态信号进行抑郁障碍的自动识别与预测。',
    '- **AI4Science**：将人工智能方法应用于科学研究，探索跨学科的前沿问题。',
    '',
    '近年在步态识别领域形成了从步态特征学习（GaitSet, GaitPart）到跨视角泛化（GaitGL, CSTL）、从轮廓图到三维姿态（PoseGait, GPGait++）的完整技术体系，并在 IEEE TPAMI、CVPR、NeurIPS 等顶级期刊/会议发表系列论文。',
    '',
    '---',
    '',
]

lines = lines[:idx_section4] + cv_section + lines[idx_section4:]

# Recalculate section 8 index after insertion
idx_section8 = None
for i, l in enumerate(lines):
    if l.startswith('## 8. '):
        idx_section8 = i
        break

# 4. Replace stage narrative placeholders with proper narratives
narratives = {
    '4.1 2005–2009': '博士阶段前后，主要探索生物启发视觉模型（Enhanced Biologically Inspired Model）、图像分类与目标检测的基础方法，为后续在计算机视觉领域的研究奠定基础。',
    '4.2 2010–2014': '就职中科院自动化所后，研究重点转向目标检测（Deformable Part Model、语义窗口挖掘）和图像分类的特征编码方法。2013 年起逐步切入步态识别，构建 RGB-D 步态数据集及基线算法。',
    '4.3 2015–2019': '步态识别取得多项突破性成果：提出 GaitSet（基于集合的步态特征学习）、GaitPart（时序部位模型）、GaitGL（全局-局部特征融合）等框架，在 CASIA 步态数据集上大幅提升识别率。同时探索生成对抗网络在步态特征提取中的应用（GaitGANv2），以及基于三维姿态的步态识别（PoseGait）方法。',
    '4.4 2020–2024': '研究从步态识别扩展至更广泛的多模态感知领域：发表 Set Residual Network、CSTL（跨视角步态识别）等工作，组织 HID 远距离身份识别竞赛。同时开辟抑郁识别的视觉分析方向，利用步态和面部信号进行抑郁风险评估。多模态大模型与 AI4Science 方向也开始布局。',
    '4.5 2025–2029': '加入北京师范大学后，继续推进步态识别向多模态融合（MMGait）、词汇引导（Vocabulary-Guided Gait Recognition）、无监督学习（Multimodal Mutual Learning）方向发展。同时拓展具身智能（Continual Learning VLA Models）和深度学习驱动的抑郁诊断研究。',
}

for i, l in enumerate(lines):
    if '<!--' in l and 'AI ' in l and '-->' in l:
        # Find which stage this belongs to by looking backward
        for j in range(i-5, i):
            for stage, narrative in narratives.items():
                if stage in lines[j]:
                    lines[i] = narrative
                    break

# 5. Remove circRNA pollution papers and retraction notice
skip_patterns = [
    'Table S1 CircRNAs',
    'Table S2 Significantly enriched pathway',
    'Table S3 List of 8',
    'Retraction Notice to: circFGFR4',
]
cleaned = []
for l in lines:
    skip = False
    for pat in skip_patterns:
        if pat in l and '|' in l:
            skip = True
            break
    if not skip:
        cleaned.append(l)
lines = cleaned

# 6. Recalculate section 8 index after changes
idx_section8 = None
for i, l in enumerate(lines):
    if l.startswith('## 8. '):
        idx_section8 = i
        break

# 7. Insert sections 5, 6, 7, 9 before section 8
extra = [
    '---',
    '',
    '## 5. 合作网络',
    '',
    '| 合作者 | 机构 | 合作方向 |',
    '|:-------|:-----|:---------|',
    '| 谭铁牛（Tieniu Tan） | 中国科学院自动化研究所 | 博士导师，早期目标检测与图像分类研究 |',
    '| 王亮（Liang Wang） | 中国科学院自动化研究所 | 步态识别、行人再识别 |',
    '| 侯赛辉（Saihui Hou） | 北京师范大学 | 步态识别核心合作者，GaitSet/GaitPart/GaitGL 系列 |',
    '| 曹春水（Chunshui Cao） | 银河水滴科技 | 步态识别产业化合作 |',
    '| 刘旭（Xu Liu） | 银河水滴科技 | 步态识别应用研究 |',
    '| 胡学财（Xuecai Hu） | 北京师范大学 | 多模态感知研究 |',
    '',
    '---',
    '',
    '## 6. 公开信息',
    '',
    '### 学术兼职',
    '- IEEE / CVF 多个国际会议程序委员会委员（CVPR, ICCV, ECCV, AAAI, NeurIPS 等）',
    '- 期刊 Neurocomputing 编委',
    '- 中国图象图形学学会理事兼视觉应用专委会副主任',
    '- 中国人工智能学会模式识别专委会委员',
    '- 中国计算机学会计算机视觉专委会委员',
    '',
    '### 荣誉与奖励',
    '- 2025 斯坦福大学全球前 2% 顶尖科学家榜单',
    '- 入选教育部人才计划、北京市科技新星',
    '- 北京市科学技术二等奖',
    '- 中国图象图形学学会科学技术二等奖',
    '- 中国科学院科技成果转化一等奖',
    '- 中国专利优秀奖',
    '- 微软 MVP（Most Valuable Professional）',
    '',
    '### 代表性项目',
    '- 国家自然科学基金面上项目（远距离步态识别，2023–2026）',
    '- 国家重点研发计划项目（多模态感知与计算）',
    '- 教育部卓越博士导师项目（非模态生物特征预测研究，2025–2027）',
    '- 北京市科委项目（生成式人工智能数据安全关键技术研究，2023–2025）',
    '',
    '---',
    '',
    '## 7. 验证来源',
    '',
    '| 来源 | URL |',
    '|:-----|:----|',
    '| 北京师范大学教师主页 | https://ai.bnu.edu.cn/xygk/szdw/zgj/bfed57e2f8fc4de2a6b370063517f801.htm |',
    '| Google Scholar | https://scholar.google.com/citations?user=OH7-k7oAAAAJ&hl=en |',
    '| OpenAlex | https://openalex.org/authors/A5024579621 |',
    '| ORCID | https://orcid.org/0000-0003-4389-9805 |',
    '',
    '---',
    '',
]

lines = lines[:idx_section8] + extra + lines[idx_section8:]

# 8. Renumber sections - find the right section 9 for data quality
# After inserting 5,6,7 before 8, the original section 8 is still "8. 数据质量说明"
# Let's renumber it to "9. 数据质量说明"
idx_data_quality = None
for i, l in enumerate(lines):
    if l.startswith('## 8. '):
        lines[i] = l.replace('## 8. ', '## 9. ', 1)
        idx_data_quality = i
        break

# Write back
output = '\n'.join(lines)
with open(profile_path, 'w', encoding='utf-8') as f:
    f.write(output)
with open(archive_path, 'w', encoding='utf-8') as f:
    f.write(output)

paper_count = len([l for l in lines if l.strip().startswith('|') and '[' in l and '](http' in l])
print(f"Profile written: {len(output)} chars, {len(lines)} lines")
print(f"Estimated paper count in tables: {paper_count}")
