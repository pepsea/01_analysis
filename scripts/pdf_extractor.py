"""
PDF論文テキスト・メタデータ抽出モジュール

PDFファイルからテキストとメタデータを抽出し、
Claude Projects にアップロード可能な形式で出力する。
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

try:
    import pymupdf as fitz  # PyMuPDF (新しいimport名)
except ImportError:
    try:
        import fitz  # PyMuPDF (従来のimport名)
    except ImportError:
        print("エラー: PyMuPDF が必要です。以下でインストールしてください:")
        print("  pip install pymupdf")
        sys.exit(1)


@dataclass
class PaperMetadata:
    """論文のメタデータ"""
    title: str = ""
    authors: str = ""
    journal: str = ""
    year: str = ""
    doi: str = ""
    pages: int = 0
    filename: str = ""


@dataclass
class ExtractedPaper:
    """抽出された論文データ"""
    metadata: PaperMetadata = field(default_factory=PaperMetadata)
    full_text: str = ""
    sections: dict = field(default_factory=dict)


def extract_text_from_pdf(pdf_path: str) -> ExtractedPaper:
    """
    PDFファイルからテキストとメタデータを抽出する。

    Args:
        pdf_path: PDFファイルのパス

    Returns:
        ExtractedPaper: 抽出された論文データ
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"PDFファイルではありません: {pdf_path}")

    doc = fitz.open(str(path))
    paper = ExtractedPaper()

    # メタデータ抽出
    paper.metadata = _extract_metadata(doc, path)

    # 全文テキスト抽出
    pages_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text)

    paper.full_text = "\n\n".join(pages_text)

    # セクション分割を試みる
    paper.sections = _split_sections(paper.full_text)

    doc.close()
    return paper


def _extract_metadata(doc, path: Path) -> PaperMetadata:
    """PDFメタデータとテキストからメタデータを抽出"""
    meta = PaperMetadata()
    meta.filename = path.name
    meta.pages = len(doc)

    # PDF組み込みメタデータ
    pdf_meta = doc.metadata
    if pdf_meta:
        meta.title = pdf_meta.get("title", "") or ""
        meta.authors = pdf_meta.get("author", "") or ""

    # タイトルが空の場合、最初のページから推定
    if not meta.title.strip():
        first_page = doc[0].get_text("text")
        lines = [l.strip() for l in first_page.split("\n") if l.strip()]
        if lines:
            # 最初の非空行をタイトル候補とする
            meta.title = lines[0]

    # DOI抽出（テキスト全体から検索）
    full_text = ""
    for page_num in range(min(3, len(doc))):  # 最初の3ページから検索
        full_text += doc[page_num].get_text("text")

    doi_match = re.search(r'(10\.\d{4,}/[^\s]+)', full_text)
    if doi_match:
        meta.doi = doi_match.group(1).rstrip(".,;)")

    # 年の抽出
    year_match = re.search(r'(20[0-2]\d|19\d{2})', full_text)
    if year_match:
        meta.year = year_match.group(1)

    return meta


# 論文の一般的なセクション見出しパターン
SECTION_PATTERNS = [
    r'(?i)^(abstract|要旨)',
    r'(?i)^(introduction|序論|はじめに)',
    r'(?i)^(materials?\s+and\s+methods?|methods?|方法|実験方法)',
    r'(?i)^(results?|結果)',
    r'(?i)^(discussion|考察)',
    r'(?i)^(results?\s+and\s+discussion|結果と考察)',
    r'(?i)^(conclusion|conclusions?|結論|まとめ)',
    r'(?i)^(references?|参考文献|引用文献)',
    r'(?i)^(acknowledgements?|謝辞)',
    r'(?i)^(supplementary|supporting\s+information|補足)',
]


def _split_sections(text: str) -> dict:
    """テキストをセクションに分割する"""
    sections = {}
    current_section = "header"
    current_text = []

    for line in text.split("\n"):
        stripped = line.strip()
        matched = False

        for pattern in SECTION_PATTERNS:
            if re.match(pattern, stripped):
                # 前のセクションを保存
                if current_text:
                    sections[current_section] = "\n".join(current_text).strip()
                # 新セクション開始
                current_section = stripped
                current_text = []
                matched = True
                break

        if not matched:
            current_text.append(line)

    # 最後のセクション保存
    if current_text:
        sections[current_section] = "\n".join(current_text).strip()

    return sections


def paper_to_text(paper: ExtractedPaper) -> str:
    """
    抽出した論文データをClaudeに渡すためのプレーンテキストに変換する。

    Args:
        paper: ExtractedPaper オブジェクト

    Returns:
        整形されたテキスト
    """
    lines = []
    meta = paper.metadata

    lines.append("=" * 60)
    lines.append("論文テキスト抽出結果")
    lines.append("=" * 60)
    lines.append("")

    # メタデータ
    lines.append("【メタデータ】")
    if meta.title:
        lines.append(f"  タイトル: {meta.title}")
    if meta.authors:
        lines.append(f"  著者: {meta.authors}")
    if meta.journal:
        lines.append(f"  雑誌: {meta.journal}")
    if meta.year:
        lines.append(f"  年: {meta.year}")
    if meta.doi:
        lines.append(f"  DOI: {meta.doi}")
    lines.append(f"  ページ数: {meta.pages}")
    lines.append(f"  ファイル: {meta.filename}")
    lines.append("")

    # セクション構成
    if paper.sections:
        lines.append("【検出されたセクション】")
        for section_name in paper.sections:
            char_count = len(paper.sections[section_name])
            lines.append(f"  - {section_name} ({char_count}文字)")
        lines.append("")

    # 本文
    lines.append("=" * 60)
    lines.append("本文")
    lines.append("=" * 60)
    lines.append("")
    lines.append(paper.full_text)

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python pdf_extractor.py <PDFファイルパス>")
        print("例:     python pdf_extractor.py papers/sample.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    paper = extract_text_from_pdf(pdf_path)
    print(paper_to_text(paper))
