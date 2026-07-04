import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PHASE1 = os.path.join(ROOT, "src", "phase1")
sys.path.insert(0, PHASE1)

import render_profile
import apply_identity_review
import apply_paper_review
import risk_gate
import step4_arxiv_id
import step5_arxiv
import step2_gs
import utils
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
        return f"""# 张三 (San Zhang) — 基础画像

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

    def test_render_profile_prof_dir_default_output_uses_profile_path(self):
        parser_output_default = render_profile.default_output_path("output/大学/所/部门/张三", None)
        self.assertEqual(
            os.path.normpath("output/大学/所/部门/张三/01_基础画像.md"),
            os.path.normpath(parser_output_default),
        )

        explicit_output = render_profile.default_output_path(
            "output/大学/所/部门/张三",
            "custom.md",
        )
        self.assertEqual("custom.md", explicit_output)

    def test_phase1_init_writes_state_inside_internal_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = os.path.join(PHASE1, "phase1_init.py")

            result = subprocess.run(
                [
                    sys.executable,
                    script,
                    "--university",
                    "测试大学",
                    "--institute",
                    "测试所",
                    "--department",
                    "测试部门",
                    "--name",
                    "张三",
                ],
                cwd=tmp,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            prof_dir = os.path.join(tmp, "output", "测试大学", "测试所", "测试部门", "张三")
            internal_dir = os.path.join(prof_dir, "_internal")
            latest_path = os.path.join(internal_dir, "latest.txt")
            archive_root = os.path.join(internal_dir, "archive")

            self.assertTrue(os.path.isdir(internal_dir))
            self.assertTrue(os.path.isfile(latest_path))
            self.assertFalse(os.path.exists(os.path.join(prof_dir, "latest.txt")))
            stdout_archive = os.path.normpath(os.path.join(tmp, result.stdout.strip()))
            self.assertTrue(stdout_archive.startswith(os.path.normpath(archive_root)))

    def test_prof_dir_resolver_uses_internal_state_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = os.path.join(tmp, "output", "大学", "所", "部门", "张三")
            internal_dir = os.path.join(prof_dir, "_internal")
            os.makedirs(internal_dir)
            with open(os.path.join(internal_dir, "latest.txt"), "w", encoding="utf-8") as f:
                f.write("20260704_010203\n")

            resolver = utils.ProfDirResolver(prof_dir)

            self.assertEqual("20260704_010203", resolver.ts)
            self.assertEqual(
                os.path.normpath(os.path.join(internal_dir, "archive", "20260704_010203")),
                os.path.normpath(resolver.archive_dir),
            )
            self.assertEqual(
                os.path.normpath(os.path.join(prof_dir, "01_基础画像.md")),
                os.path.normpath(resolver.profile_path),
            )

    def test_render_profile_omits_internal_archive_path_from_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "01_基础画像.md")
            data = {
                "professor": {
                    "name": "张三 (San Zhang)",
                    "affiliation": "测试机构",
                    "email_domain": "iphy.ac.cn",
                    "gs_id": "abc123",
                    "oa_id": "A123",
                },
                "papers": [],
                "statistics": {},
                "source_status": {
                    "google_scholar": "success",
                    "openalex": "success",
                    "arxiv": "success",
                },
            }

            content = render_profile.generate(
                data,
                output_path,
                run_timestamp="20260704_010203",
            )

        self.assertTrue(content.startswith("# 张三 (San Zhang) — 基础画像"))
        self.assertNotIn("run_timestamp:", content)
        self.assertNotIn("source_updated:", content)
        self.assertNotIn("affiliation:", content.split("#", 1)[0])
        self.assertIn("## 资料概览", content)
        self.assertIn("Google Scholar 记录", content)
        self.assertIn("OpenAlex 记录", content)
        self.assertIn("arXiv 记录", content)
        self.assertIn("已核验，用作作者自维护论文主源", content)
        self.assertIn("| Google Scholar | 已核验 |", content)
        self.assertIn("| OpenAlex | 已核验 |", content)
        self.assertIn("| arXiv | 已核验 |", content)
        self.assertIn("| Google Scholar ID | abc123 |", content)
        self.assertIn("| OpenAlex ID | A123 |", content)
        self.assertNotIn("Google Scholar 数据", content)
        self.assertNotIn("已采集", content)
        self.assertNotIn("同名噪声", content)
        self.assertNotIn("合并后", content)
        self.assertNotIn("| GS ID |", content)
        self.assertNotIn("| OA ID |", content)
        self.assertNotIn("run_archive:", content)
        self.assertNotIn("运行存档", content)
        self.assertNotIn("## 运行信息", content)
        self.assertNotIn("生成时间", content)
        self.assertNotIn("GS 状态", content)
        self.assertNotIn("archive/20260704_010203", content)

    def test_verify_profile_fails_when_yaml_frontmatter_is_visible(self):
        profile_path = self._write_profile(
            """---
affiliation: 测试机构
run_timestamp: 20260704_010203
---

""" + self._valid_profile()
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("不使用裸露 frontmatter", buf.getvalue())

    def test_verify_profile_fails_when_html_comment_is_visible(self):
        profile_path = self._write_profile(
            self._valid_profile().replace(
                "## 5. 合作网络",
                "<!-- 已被剔除的同名噪声 -->\n## 5. 合作网络",
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("不含 HTML 注释", buf.getvalue())

    def test_verify_profile_accepts_current_stage_title_to_present(self):
        profile_path = self._write_profile(
            self._valid_profile().replace(
                "### 4.2 博后阶段（2012–2013）",
                "### 4.2 博后阶段（2012–至今）",
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.PASS, result, buf.getvalue())

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

    def test_scholarly_to_paper_adds_google_scholar_publication_url(self):
        paper = step2_gs._scholarly_to_paper(
            {
                "author_pub_id": "abc123:pub456",
                "num_citations": 7,
                "bib": {
                    "title": "A GS-only paper",
                    "pub_year": "2024",
                    "citation": "Test Journal",
                },
            },
            "abc123",
        )

        self.assertEqual(
            "https://scholar.google.com/citations?view_op=view_citation&hl=en&user=abc123&citation_for_view=abc123:pub456",
            paper["url"],
        )

    def test_make_paper_link_uses_url_when_doi_and_arxiv_are_missing(self):
        link = utils.make_paper_link(
            {
                "title": "A GS-only paper",
                "doi": None,
                "arxiv_id": None,
                "url": "https://scholar.google.com/citations?view_op=view_citation&user=abc123",
            }
        )

        self.assertEqual(
            "[A GS-only paper](https://scholar.google.com/citations?view_op=view_citation&user=abc123)",
            link,
        )

    def test_risk_gate_load_json_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = os.path.join(tmp, "data.json")
            with open(json_path, "w", encoding="utf-8-sig") as f:
                f.write('{"ok": true}')

            data = risk_gate.load_json(json_path)

        self.assertEqual({"ok": True}, data)
    def test_risk_gate_passes_standard_when_identity_and_sources_are_stable(self):
        merged = {
            "professor": {"name": "张三 (San Zhang)", "email_domain": "iphy.ac.cn"},
            "papers": [
                {"title": "A", "sources": ["google_scholar", "openalex"]},
                {"title": "B", "sources": ["google_scholar"]},
                {"title": "C", "sources": ["google_scholar"]},
                {"title": "D", "sources": ["google_scholar"]},
            ],
            "statistics": {"by_source": {"google_scholar": 4, "openalex": 1}},
        }
        verified_ids = {
            "name": "张三 (San Zhang)",
            "verification": {"tier": "T1", "email_domain": "iphy.ac.cn"},
            "ids": {"gs_id": "abc", "oa_id": "A123"},
        }

        result = risk_gate.evaluate_risk(merged, verified_ids)

        self.assertEqual("standard", result.mode)
        self.assertEqual([], result.reasons)
        self.assertEqual([], result.actions)

    def test_risk_gate_requires_conservative_when_single_source_ratio_is_high(self):
        merged = {
            "professor": {"name": "张三 (San Zhang)", "email_domain": "iphy.ac.cn"},
            "papers": [
                {"title": "GS confirmed", "sources": ["google_scholar", "openalex"]},
                {"title": "OA only 1", "sources": ["openalex"]},
                {"title": "OA only 2", "sources": ["openalex"]},
            ],
            "statistics": {"by_source": {"google_scholar": 1, "openalex": 3}},
        }
        verified_ids = {
            "name": "张三 (San Zhang)",
            "verification": {"tier": "T1", "email_domain": "iphy.ac.cn"},
            "ids": {"gs_id": "abc", "oa_id": "A123"},
        }

        result = risk_gate.evaluate_risk(merged, verified_ids)

        self.assertEqual("conservative_required", result.mode)
        self.assertIn("single-source OA/arXiv ratio", "\n".join(result.reasons))
        self.assertIn("逐篇核查 OA/arXiv-only 论文", "\n".join(result.actions))

    def test_risk_gate_requires_conservative_when_identity_evidence_is_weak(self):
        merged = {
            "professor": {"name": "张三", "email_domain": "iphy.ac.cn"},
            "papers": [{"title": "A", "sources": ["google_scholar"]}],
            "statistics": {"by_source": {"google_scholar": 1}},
        }
        verified_ids = {
            "name": "张三",
            "verification": {"tier": "T4"},
            "ids": {},
        }

        result = risk_gate.evaluate_risk(merged, verified_ids)

        self.assertEqual("conservative_required", result.mode)
        self.assertIn("English name missing", "\n".join(result.reasons))
        self.assertIn("verification tier is T4", "\n".join(result.reasons))
        self.assertIn("补官网英文名", "\n".join(result.actions))
        self.assertIn("重新做身份锁定", "\n".join(result.actions))

    def test_risk_gate_prints_next_actions_for_conservative_mode(self):
        result = risk_gate.RiskResult(
            mode="conservative_required",
            reasons=["English name missing from professor/verified_ids name"],
            actions=["补官网英文名，保持 中文名 (English Name) 格式。"],
            metrics={"total_papers": 1},
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            risk_gate.print_result(result)

        output = buf.getvalue()
        self.assertIn("next_actions:", output)
        self.assertIn("补官网英文名", output)

    def test_risk_gate_prints_single_source_oa_arxiv_papers(self):
        papers = [
            {
                "title": "OA-only paper",
                "year": 2024,
                "doi": "https://doi.org/10.1000/oa",
                "authors": ["San Zhang", "Li Wang"],
                "sources": ["openalex"],
            },
            {
                "title": "GS confirmed paper",
                "year": 2023,
                "doi": "https://doi.org/10.1000/gs",
                "sources": ["google_scholar", "openalex"],
            },
            {
                "title": "arXiv-only paper",
                "year": 2022,
                "arxiv_id": "2201.00001",
                "sources": ["arxiv"],
            },
        ]

        buf = io.StringIO()
        with redirect_stdout(buf):
            risk_gate.print_single_source_papers(papers)

        output = buf.getvalue()
        self.assertIn("single_source_oa_arxiv_papers:", output)
        self.assertIn("2024 | OA-only paper | https://doi.org/10.1000/oa | San Zhang; Li Wang", output)
        self.assertIn("2022 | arXiv-only paper | arXiv:2201.00001", output)
        self.assertNotIn("GS confirmed paper", output)

    def test_apply_identity_review_updates_active_verified_ids_and_merged_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = os.path.join(tmp, "output", "大学", "所", "部门", "张三")
            archive_dir = os.path.join(prof_dir, "_internal", "archive", "20260704_120000")
            os.makedirs(archive_dir)
            os.makedirs(os.path.join(prof_dir, "_internal"), exist_ok=True)
            with open(os.path.join(prof_dir, "_internal", "latest.txt"), "w", encoding="utf-8") as f:
                f.write("20260704_120000\n")
            verified_path = os.path.join(archive_dir, "00_verified_ids.json")
            merged_path = os.path.join(archive_dir, "04_merged.json")
            with open(verified_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "name": "张三",
                        "name_pinyin": "Zhang_San",
                        "ids": {"gs_id": "abc", "oa_id": "A123", "orcid": "0000-0000-0000-0000"},
                        "verification": {"tier": "T2", "email_domain": "old.edu", "gs_email_verified": False},
                        "sources": {},
                    },
                    f,
                    ensure_ascii=False,
                )
            with open(merged_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "professor": {"name": "张三", "email_domain": "old.edu"},
                        "papers": [],
                        "statistics": {"by_source": {}},
                    },
                    f,
                    ensure_ascii=False,
                )

            apply_identity_review.apply_identity_review(
                prof_dir=prof_dir,
                display_name="张三 (San Zhang)",
                official_email_domain="iphy.ac.cn",
                official_affiliation="测试研究所",
                official_url="https://example.edu/profile",
                note="official profile confirms English name and current email",
            )

            with open(verified_path, "r", encoding="utf-8-sig") as f:
                verified = json.load(f)
            with open(merged_path, "r", encoding="utf-8-sig") as f:
                merged = json.load(f)

        self.assertEqual("张三 (San Zhang)", verified["name"])
        self.assertEqual("iphy.ac.cn", verified["verification"]["email_domain"])
        self.assertEqual("https://example.edu/profile", verified["sources"]["official_profile_url"])
        self.assertEqual("张三 (San Zhang)", merged["professor"]["name"])
        self.assertEqual("iphy.ac.cn", merged["professor"]["email_domain"])
        self.assertEqual("测试研究所", merged["professor"]["affiliation"])
        self.assertEqual("测试研究所", merged["metadata"]["identity_review"]["official_affiliation"])
        self.assertEqual("https://example.edu/profile", merged["metadata"]["identity_review"]["official_url"])

    def test_apply_paper_review_excludes_doi_and_recomputes_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = os.path.join(tmp, "output", "大学", "所", "部门", "张三")
            archive_dir = os.path.join(prof_dir, "_internal", "archive", "20260704_120000")
            os.makedirs(archive_dir)
            os.makedirs(os.path.join(prof_dir, "_internal"), exist_ok=True)
            with open(os.path.join(prof_dir, "_internal", "latest.txt"), "w", encoding="utf-8") as f:
                f.write("20260704_120000\n")
            merged_path = os.path.join(archive_dir, "04_merged.json")
            with open(merged_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "professor": {"name": "张三 (San Zhang)"},
                        "papers": [
                            {
                                "title": "GS paper",
                                "doi": "https://doi.org/10.1000/keep",
                                "sources": ["google_scholar", "openalex"],
                            },
                            {
                                "title": "OA same-name noise",
                                "doi": "https://doi.org/10.1000/noise",
                                "sources": ["openalex"],
                            },
                        ],
                        "statistics": {"total": 2, "unique": 2, "by_source": {"google_scholar": 1, "openalex": 2}},
                    },
                    f,
                    ensure_ascii=False,
                )

            apply_paper_review.exclude_papers_by_doi(
                prof_dir=prof_dir,
                dois=["10.1000/noise"],
                reason="same-name noise",
                source_url="https://example.edu/review",
            )

            with open(merged_path, "r", encoding="utf-8-sig") as f:
                merged = json.load(f)

        self.assertEqual(["GS paper"], [paper["title"] for paper in merged["papers"]])
        self.assertEqual(1, merged["statistics"]["total"])
        self.assertEqual({"google_scholar": 1, "openalex": 1}, merged["statistics"]["by_source"])
        excluded = merged["metadata"]["paper_review"]["excluded"]
        self.assertEqual("OA same-name noise", excluded[0]["title"])
        self.assertEqual("same-name noise", excluded[0]["reason"])
        self.assertEqual("https://example.edu/review", excluded[0]["source_url"])

    def test_step4_arxiv_id_accepts_prof_dir_and_writes_current_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = os.path.join(tmp, "output", "大学", "所", "部门", "张三")
            internal_dir = os.path.join(prof_dir, "_internal")
            archive_dir = os.path.join(internal_dir, "archive", "20260704_120000")
            os.makedirs(archive_dir)
            with open(os.path.join(internal_dir, "latest.txt"), "w", encoding="utf-8") as f:
                f.write("20260704_120000\n")

            result = {
                "pipeline": "phase1",
                "source": "arxiv",
                "status": "empty",
                "error": None,
                "professor": None,
                "papers": [],
                "metadata": {"method": "author_id_feed"},
            }

            argv = [
                "step4_arxiv_id.py",
                "0000-0002-3228-9932",
                "--name",
                "Zhang_San",
                "--prof-dir",
                prof_dir,
            ]
            with patch.object(sys, "argv", argv), patch.object(
                step4_arxiv_id, "fetch_by_orcid", return_value=result
            ) as fetch_mock:
                step4_arxiv_id.main()

            output_path = os.path.join(archive_dir, "03_arxiv.json")
            with open(output_path, "r", encoding="utf-8-sig") as f:
                written = json.load(f)

        fetch_mock.assert_called_once_with("0000-0002-3228-9932", "Zhang_San")
        self.assertEqual("arxiv", written["source"])
        self.assertEqual([], written["papers"])

    def test_step5_arxiv_accepts_prof_dir_and_writes_current_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_dir = os.path.join(tmp, "output", "大学", "所", "部门", "张三")
            internal_dir = os.path.join(prof_dir, "_internal")
            archive_dir = os.path.join(internal_dir, "archive", "20260704_120000")
            os.makedirs(archive_dir)
            with open(os.path.join(internal_dir, "latest.txt"), "w", encoding="utf-8") as f:
                f.write("20260704_120000\n")

            result = {
                "pipeline": "phase1",
                "source": "arxiv",
                "status": "empty",
                "error": None,
                "professor": None,
                "papers": [],
                "metadata": {"query": "Zhang_San"},
            }

            argv = [
                "step5_arxiv.py",
                "Zhang_San",
                "--categories",
                "physics.atom-ph",
                "--prof-dir",
                prof_dir,
            ]
            with patch.object(sys, "argv", argv), patch.object(
                step5_arxiv, "search", return_value=result
            ) as search_mock:
                step5_arxiv.main()

            output_path = os.path.join(archive_dir, "03_arxiv.json")
            with open(output_path, "r", encoding="utf-8-sig") as f:
                written = json.load(f)

        search_mock.assert_called_once_with("Zhang_San", 200, categories="physics.atom-ph")
        self.assertEqual("arxiv", written["source"])
        self.assertEqual([], written["papers"])

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

    def test_verify_profile_fails_when_section9_repeats_source_table_header(self):
        profile_path = self._write_profile(
            self._valid_profile(
                """| 来源 | URL | 状态 |
|:-----|:----|:------|
| 来源 | URL | 状态 |
|:-----|:----|:------|
| 官网 | https://example.com | 已验证 |
"""
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.FAIL, result)
        self.assertIn("§9 验证来源表头只出现一次", buf.getvalue())

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

    def test_verify_profile_accepts_google_scholar_paper_links_when_doi_missing(self):
        profile_path = self._write_profile(
            self._valid_profile()
            .replace(
                "[Paper A](https://doi.org/10.1000/a)",
                "[Paper A](https://scholar.google.com/citations?view_op=view_citation&user=abc)",
            )
            .replace(
                "[Paper B](https://doi.org/10.1000/b)",
                "[Paper B](https://scholar.google.com/citations?view_op=view_citation&user=abc)",
            )
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = verify_profile.verify(profile_path)

        self.assertEqual(verify_profile.PASS, result, buf.getvalue())


if __name__ == "__main__":
    unittest.main()
