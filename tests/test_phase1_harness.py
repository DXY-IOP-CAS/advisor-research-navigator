import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PHASE1 = os.path.join(ROOT, "src", "phase1")
sys.path.insert(0, PHASE1)

import render_profile
import step2_gs
import validate_career_stages
import verify_profile


class Phase1HarnessTests(unittest.TestCase):
    def _write_profile(self, content: str) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        prof_dir = os.path.join(tmp.name, "output", "大学", "所", "部门", "张三")
        os.makedirs(prof_dir)
        profile_path = os.path.join(prof_dir, "01_基础画像.md")
        with open(profile_path, "w", encoding="utf-8") as f:
            f.write(content)
        return profile_path

    def _valid_profile(self, section9: str = None) -> str:
        if section9 is None:
            section9 = """| 来源 | URL | 状态 |
|:-----|:----|:------|
| 官网 | https://example.com | 已验证 |
"""
        return f"""---
affiliation: 测试机构
---

# 张三 (San Zhang) — 基础画像

## 1. 身份标识

| 字段 | 内容 |
|:-----|:------|
| 姓名 | 张三 (San Zhang) |
| 机构 | 测试机构 |
| 邮箱 | ...@iphy.ac.cn |

---

## 2. 学术履历

| 时间 | 机构 | 职位 | 方向 |
|:-----|:-----|:-----|:------|
| 2010–2011 | 测试大学 | 博士研究生 | 测试方向 |
| 2012–2013 | 测试大学 | 博士后 | 测试方向 |
| 2014–2015 | 测试机构 | 研究员 | 测试方向 |

## 3. 研究方向

测试研究方向。

## 4. 全部论文（按学术履历阶段分组）

### 4.1 博士阶段（2010–2011）

测试叙事。

论文数：1 篇

| # | 年份 | 标题 | 期刊 | 引用 | 来源 |
|:--|:----|:-----|:-----|:----|:-----|
| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | GS |

### 4.2 博后阶段（2012–2013）

测试叙事。

论文数：1 篇

| # | 年份 | 标题 | 期刊 | 引用 | 来源 |
|:--|:----|:-----|:-----|:----|:-----|
| 1 | 2012 | [Paper B](https://doi.org/10.1000/b) | Journal | 2 | GS |

## 5. 合作网络

测试合作网络。

## 6. 公开信息

测试公开信息。

## 7. 引用与影响力分析

测试引用分析。

## 8. 数据质量说明

| 数据源 | 状态 | 论文数 | 说明 |
|:-------|:----:|:------:|:-----|
| Google Scholar | success | 2 | 测试 |

## 9. 验证来源

{section9}"""

    def test_render_profile_accepts_dict_wrapped_career_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "01_基础画像.md")
            data = {
                "professor": {
                    "name": "张三 (San Zhang)",
                    "affiliation": "测试机构",
                    "email_domain": "iphy.ac.cn",
                    "gs_id": "abc123",
                },
                "papers": [
                    {
                        "title": "A tested paper",
                        "year": 2010,
                        "journal": "Test Journal",
                        "citation_count": 1,
                        "doi": "10.1000/test",
                        "sources": ["google_scholar"],
                        "source_count": 1,
                    }
                ],
                "statistics": {},
                "source_status": {},
            }
            stages = {
                "stages": [
                    {
                        "name": "博士阶段",
                        "start": 2010,
                        "end": 2011,
                        "institution": "测试大学",
                        "position": "博士研究生",
                        "direction": "测试方向",
                    }
                ]
            }

            content = render_profile.generate(data, output_path, stages)

            self.assertIn("## 2. 学术履历", content)
            self.assertIn("| 2010–2011 | 测试大学 | 博士研究生 | 测试方向 |", content)
            self.assertIn("### 4.1 博士阶段（2010–2011）", content)

    def test_validate_career_stages_accepts_dict_wrapped_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            stages_path = os.path.join(tmp, "career_stages.json")
            with open(stages_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "stages": [
                            {
                                "name": "博士阶段",
                                "start": 2010,
                                "end": 2011,
                                "institution": "测试大学",
                                "position": "博士研究生",
                                "direction": "测试方向",
                            }
                        ]
                    },
                    f,
                    ensure_ascii=False,
                )

            buf = io.StringIO()
            with redirect_stdout(buf):
                result = validate_career_stages.validate(stages_path)

            self.assertEqual(validate_career_stages.PASS, result)
            self.assertIn("[OK] 根元素是数组", buf.getvalue())

    def test_normalize_email_domain_removes_truncated_local_part(self):
        self.assertEqual("iphy.ac.cn", step2_gs.normalize_email_domain("...@@iphy.ac.cn"))
        self.assertEqual("iphy.ac.cn", step2_gs.normalize_email_domain("@iphy.ac.cn"))
        self.assertEqual("iphy.ac.cn", step2_gs.normalize_email_domain("Verified email at iphy.ac.cn"))

    def test_verify_profile_fails_when_identity_table_name_is_not_mixed(self):
        profile_path = self._write_profile(
            self._valid_profile().replace("| 姓名 | 张三 (San Zhang) |", "| 姓名 | San Zhang |")
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("§1 姓名字段", buf.getvalue())

    def test_verify_profile_fails_when_section9_uses_bullet_list(self):
        profile_path = self._write_profile(
            self._valid_profile(
                """| 来源 | URL | 状态 |
|:-----|:----|:------|

- 官网：https://example.com（已验证）
"""
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("§9 验证来源不用列表格式", buf.getvalue())

    def test_verify_profile_fails_when_section9_contains_unverified_linkedin(self):
        profile_path = self._write_profile(
            self._valid_profile(
                """| 来源 | URL | 状态 |
|:-----|:----|:------|
| 官网 | https://example.com | 已验证 |
| LinkedIn | https://linkedin.com/in/example | 未验证 |
"""
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("§9 验证来源不含未验证来源", buf.getvalue())

    def test_verify_profile_fails_when_single_source_oa_row_is_unvetted(self):
        profile_path = self._write_profile(
            self._valid_profile().replace(
                "| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | GS |",
                "| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | OA |",
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("单源 OA/arXiv 论文需人工核查", buf.getvalue())

    def test_verify_profile_fails_when_single_source_row_is_only_pending_review(self):
        profile_path = self._write_profile(
            self._valid_profile().replace(
                "| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | GS |",
                "| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | OA（待核查） |",
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("单源 OA/arXiv 论文需人工核查", buf.getvalue())

    def test_verify_profile_allows_single_source_row_after_manual_review(self):
        profile_path = self._write_profile(
            self._valid_profile().replace(
                "| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | GS |",
                "| 1 | 2010 | [Paper A](https://doi.org/10.1000/a) | Journal | 1 | OA（已核查） |",
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.PASS, result)


if __name__ == "__main__":
    unittest.main()
