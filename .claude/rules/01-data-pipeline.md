# 01 — 数据流水线（阶段 B + C）

所有 step 是独立 CLI，输入输出是 JSON 文件。不互相 import。

## 通用数据模式

每步输出的 JSON 字段格式一致（SOURCE_OUTPUT）：

```json
{
  "pipeline": "phase1",
  "source": "google_scholar | openalex | arxiv",
  "status": "success | blocked | error",
  "professor": { "name", "affiliation", "email_domain", "h_index", ... },
  "papers": [{ "title", "year", "doi", "arxiv_id", "citation_count", "source" }, ...]
}
```

step6_merge 产出 MERGED_OUTPUT，多出 `sources`（验证标记）+ `source_count` 字段。

## 阶段 B 执行

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROF="output/中科院物理所/超快物质科学中心/张鹏举"
mkdir -p "$PROF/archive/$TIMESTAMP"

# 推荐真实邮箱（非 test@example.com），否则 OpenAlex 限速 1 req/s
python src/phase1/step2_gs.py ls7XuGoAAAAJ -o "$PROF/archive/$TIMESTAMP/01_gs.json"
python src/phase1/step3_openalex.py A5000914228 --email your@real.com -o "$PROF/archive/$TIMESTAMP/02_oa.json"
python src/phase1/step5_arxiv.py "Zhang_Pengju" -c "physics.atom-ph physics.optics" -o "$PROF/archive/$TIMESTAMP/03_arxiv.json"
python src/phase1/step6_merge.py "$PROF/archive/$TIMESTAMP/01_gs.json" "$PROF/archive/$TIMESTAMP/02_oa.json" "$PROF/archive/$TIMESTAMP/03_arxiv.json" -o "$PROF/archive/$TIMESTAMP/04_merged.json"
```

## 阶段 C 渲染

```bash
python src/phase1/render_profile.py "$PROF/archive/$TIMESTAMP/04_merged.json" -o "$PROF/01_基础画像.md" --department "超快物质科学中心"

echo "$TIMESTAMP" > "$PROF/latest.txt"
```

render_profile.py 生成论文表格（含 DOI/arXiv 超链接）+ 运行统计。脚本完成后由 AI 补充：
- 学术履历表
- 研究方向描述
- 每阶段叙事（不报菜名——说明研究主题）
- 合作网络、公开信息
