"""
科学論文PDF要約ツール (Scientific Paper Summarizer)

PDFファイルから科学論文のテキストを抽出し、
セクションごとに構造化された要約を生成するモジュール。

主な機能:
- PDF からのテキスト抽出
- 論文セクション（Abstract, Introduction, Methods, Results, Discussion 等）の自動検出
- TF-IDF ベースの抽出型要約
- 構造化されたサマリーレポートの生成
"""

import re
import math
from collections import Counter
from pathlib import Path
from dataclasses import dataclass, field

from PyPDF2 import PdfReader


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------

@dataclass
class PaperSection:
    """論文の1セクションを表すデータクラス"""
    name: str
    text: str
    sentences: list[str] = field(default_factory=list)
    summary_sentences: list[str] = field(default_factory=list)


@dataclass
class PaperInfo:
    """論文全体の情報を保持するデータクラス"""
    file_path: str
    title: str = ""
    total_pages: int = 0
    raw_text: str = ""
    sections: list[PaperSection] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 定数: セクション見出しパターン
# ---------------------------------------------------------------------------

# 英語論文の一般的なセクション見出し
SECTION_PATTERNS = [
    (r"(?i)^(?:\d+\.?\s*)?abstract\b", "Abstract"),
    (r"(?i)^(?:\d+\.?\s*)?introduction\b", "Introduction"),
    (r"(?i)^(?:\d+\.?\s*)?background\b", "Background"),
    (r"(?i)^(?:\d+\.?\s*)?(?:materials?\s+and\s+)?methods?\b", "Methods"),
    (r"(?i)^(?:\d+\.?\s*)?experimental\b", "Methods"),
    (r"(?i)^(?:\d+\.?\s*)?results?\b", "Results"),
    (r"(?i)^(?:\d+\.?\s*)?results?\s+and\s+discussion\b", "Results and Discussion"),
    (r"(?i)^(?:\d+\.?\s*)?discussion\b", "Discussion"),
    (r"(?i)^(?:\d+\.?\s*)?conclusions?\b", "Conclusion"),
    (r"(?i)^(?:\d+\.?\s*)?summary\b", "Summary"),
    (r"(?i)^(?:\d+\.?\s*)?acknowledg[e]?ments?\b", "Acknowledgements"),
    (r"(?i)^(?:\d+\.?\s*)?references?\b", "References"),
    (r"(?i)^(?:\d+\.?\s*)?supplementary\b", "Supplementary"),
    (r"(?i)^(?:\d+\.?\s*)?funding\b", "Funding"),
    (r"(?i)^(?:\d+\.?\s*)?author\s+contributions?\b", "Author Contributions"),
    (r"(?i)^(?:\d+\.?\s*)?competing\s+interests?\b", "Competing Interests"),
    (r"(?i)^(?:\d+\.?\s*)?data\s+availability\b", "Data Availability"),
]

# 要約対象から除外するセクション
SKIP_SECTIONS = {
    "References", "Acknowledgements", "Supplementary",
    "Funding", "Author Contributions", "Competing Interests",
    "Data Availability",
}

# ストップワード（TF-IDF 計算で無視する一般的な英単語）
STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "not", "no", "nor", "as", "if", "than",
    "so", "such", "when", "where", "which", "who", "whom", "what", "how",
    "all", "each", "both", "more", "most", "other", "some", "any", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "also", "very", "often", "however", "further", "then", "here", "there",
    "about", "up", "out", "over", "under", "again", "once", "our", "we",
    "they", "their", "them", "he", "she", "his", "her", "you", "your",
})


# ---------------------------------------------------------------------------
# PDF テキスト抽出
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """
    PDFファイルからテキストを抽出する。

    Parameters
    ----------
    pdf_path : str
        PDFファイルのパス

    Returns
    -------
    tuple[str, int]
        (抽出されたテキスト, 総ページ数)
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"PDFファイルではありません: {pdf_path}")

    reader = PdfReader(str(path))
    total_pages = len(reader.pages)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return "\n".join(pages_text), total_pages


# ---------------------------------------------------------------------------
# タイトル推定
# ---------------------------------------------------------------------------

def _estimate_title(raw_text: str) -> str:
    """
    テキスト冒頭から論文タイトルを推定する。
    最初の数行のうち、最も長い行をタイトルとみなす簡易ヒューリスティック。
    """
    lines = [ln.strip() for ln in raw_text.split("\n")[:15] if ln.strip()]
    if not lines:
        return "(タイトル不明)"

    # 短すぎる行（著者名やジャーナル情報）を除外しつつ、最初の長い行を取る
    candidates = []
    for line in lines:
        # セクション見出しっぽい行はスキップ
        if any(re.match(pat, line) for pat, _ in SECTION_PATTERNS):
            break
        if len(line) > 10:
            candidates.append(line)
        if len(candidates) >= 3:
            break

    if not candidates:
        return lines[0]

    # 最初の候補をタイトルとする（通常、論文の最初の長い行がタイトル）
    return candidates[0]


# ---------------------------------------------------------------------------
# 文分割
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """テキストを文単位に分割する。"""
    # 略語等での誤分割を軽減するため、改行で分割してから文分割
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 文末のピリオド・?・! で分割（ただし略語 e.g., i.e., etc. に注意）
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


# ---------------------------------------------------------------------------
# セクション検出
# ---------------------------------------------------------------------------

def _detect_sections(raw_text: str) -> list[PaperSection]:
    """
    テキストからセクション見出しを検出し、セクションごとに分割する。
    """
    lines = raw_text.split("\n")
    section_breaks: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pattern, section_name in SECTION_PATTERNS:
            if re.match(pattern, stripped):
                section_breaks.append((i, section_name))
                break

    # セクションが検出されなかった場合 → 全体を1セクションとして扱う
    if not section_breaks:
        full_text = "\n".join(lines)
        return [PaperSection(
            name="Full Text",
            text=full_text,
            sentences=_split_sentences(full_text),
        )]

    sections = []
    for idx, (line_no, name) in enumerate(section_breaks):
        if idx + 1 < len(section_breaks):
            end_line = section_breaks[idx + 1][0]
        else:
            end_line = len(lines)
        section_text = "\n".join(lines[line_no:end_line])
        sections.append(PaperSection(
            name=name,
            text=section_text,
            sentences=_split_sentences(section_text),
        ))

    return sections


# ---------------------------------------------------------------------------
# TF-IDF ベースの抽出型要約
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """テキストを単語に分割し、ストップワードを除去する。"""
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def _compute_tf(words: list[str]) -> dict[str, float]:
    """単語の TF (Term Frequency) を計算する。"""
    counter = Counter(words)
    total = len(words)
    if total == 0:
        return {}
    return {w: c / total for w, c in counter.items()}


def _compute_idf(documents: list[list[str]]) -> dict[str, float]:
    """文書集合から IDF (Inverse Document Frequency) を計算する。"""
    n_docs = len(documents)
    if n_docs == 0:
        return {}
    df: Counter = Counter()
    for doc in documents:
        unique_words = set(doc)
        for w in unique_words:
            df[w] += 1
    return {w: math.log(n_docs / (1 + count)) for w, count in df.items()}


def _score_sentences(sentences: list[str], idf: dict[str, float]) -> list[tuple[float, int, str]]:
    """
    各文に TF-IDF スコアを付与する。

    Returns
    -------
    list[tuple[float, int, str]]
        (スコア, 元のインデックス, 文テキスト) のリスト（スコア降順）
    """
    scored = []
    for i, sent in enumerate(sentences):
        words = _tokenize(sent)
        if not words:
            continue
        tf = _compute_tf(words)
        score = sum(tf.get(w, 0) * idf.get(w, 0) for w in tf)
        scored.append((score, i, sent))
    scored.sort(key=lambda x: -x[0])
    return scored


def summarize_section(
    section: PaperSection,
    idf: dict[str, float],
    max_sentences: int = 3,
) -> list[str]:
    """
    セクション内の文をスコアリングし、上位の文を原文順に返す。

    Parameters
    ----------
    section : PaperSection
        要約対象のセクション
    idf : dict[str, float]
        論文全体から計算した IDF 値
    max_sentences : int
        セクションごとに抽出する文の最大数

    Returns
    -------
    list[str]
        要約として選ばれた文のリスト（原文順）
    """
    if not section.sentences:
        return []

    scored = _score_sentences(section.sentences, idf)
    top_n = scored[:max_sentences]
    # 原文での出現順にソート
    top_n.sort(key=lambda x: x[1])
    return [sent for _, _, sent in top_n]


# ---------------------------------------------------------------------------
# キーワード抽出
# ---------------------------------------------------------------------------

def extract_keywords(raw_text: str, top_n: int = 10) -> list[str]:
    """
    論文全体から TF-IDF スコア上位のキーワードを抽出する。

    Parameters
    ----------
    raw_text : str
        論文の全テキスト
    top_n : int
        取得するキーワード数

    Returns
    -------
    list[str]
        キーワードのリスト
    """
    sentences = _split_sentences(raw_text)
    docs = [_tokenize(s) for s in sentences]
    idf = _compute_idf(docs)
    all_words = _tokenize(raw_text)
    tf = _compute_tf(all_words)
    tfidf_scores = {w: tf.get(w, 0) * idf.get(w, 0) for w in tf}
    sorted_words = sorted(tfidf_scores.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:top_n]]


# ---------------------------------------------------------------------------
# メイン: 論文解析 & 要約
# ---------------------------------------------------------------------------

def analyze_paper(
    pdf_path: str,
    sentences_per_section: int = 3,
    num_keywords: int = 10,
) -> PaperInfo:
    """
    PDFファイルを読み込み、構造化された論文情報と要約を生成する。

    Parameters
    ----------
    pdf_path : str
        PDFファイルのパス
    sentences_per_section : int
        各セクションから抽出する文の数
    num_keywords : int
        抽出するキーワード数

    Returns
    -------
    PaperInfo
        解析結果を格納したデータクラス
    """
    raw_text, total_pages = extract_text_from_pdf(pdf_path)
    title = _estimate_title(raw_text)
    sections = _detect_sections(raw_text)

    # 論文全体の文をもとに IDF を計算
    all_sentences = []
    for sec in sections:
        all_sentences.extend(sec.sentences)
    all_docs = [_tokenize(s) for s in all_sentences]
    idf = _compute_idf(all_docs)

    # 各セクションの要約を生成
    for sec in sections:
        if sec.name not in SKIP_SECTIONS:
            sec.summary_sentences = summarize_section(sec, idf, sentences_per_section)

    keywords = extract_keywords(raw_text, num_keywords)

    return PaperInfo(
        file_path=pdf_path,
        title=title,
        total_pages=total_pages,
        raw_text=raw_text,
        sections=sections,
        keywords=keywords,
    )


# ---------------------------------------------------------------------------
# レポート生成
# ---------------------------------------------------------------------------

def generate_report(paper: PaperInfo) -> str:
    """
    PaperInfo から読みやすい要約レポートを生成する。

    Parameters
    ----------
    paper : PaperInfo
        analyze_paper() の戻り値

    Returns
    -------
    str
        フォーマットされた要約レポート
    """
    lines = []
    lines.append("=" * 70)
    lines.append("論文要約レポート (Paper Summary Report)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"タイトル (Title): {paper.title}")
    lines.append(f"ファイル: {paper.file_path}")
    lines.append(f"総ページ数: {paper.total_pages}")
    lines.append(f"検出セクション数: {len(paper.sections)}")
    lines.append("")

    # キーワード
    if paper.keywords:
        lines.append("-" * 40)
        lines.append("キーワード (Keywords)")
        lines.append("-" * 40)
        lines.append(", ".join(paper.keywords))
        lines.append("")

    # セクション別要約
    for sec in paper.sections:
        if sec.name in SKIP_SECTIONS:
            continue
        lines.append("-" * 40)
        lines.append(f"[{sec.name}]")
        lines.append("-" * 40)
        if sec.summary_sentences:
            for i, sent in enumerate(sec.summary_sentences, 1):
                lines.append(f"  {i}. {sent}")
        else:
            lines.append("  (要約文なし)")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def summarize_paper(
    pdf_path: str,
    sentences_per_section: int = 3,
    num_keywords: int = 10,
    print_report: bool = True,
) -> PaperInfo:
    """
    論文PDFを読み込み、要約を生成して表示するワンストップ関数。

    Parameters
    ----------
    pdf_path : str
        PDFファイルのパス
    sentences_per_section : int
        各セクションから抽出する文の数
    num_keywords : int
        抽出するキーワード数
    print_report : bool
        レポートを標準出力に表示するかどうか

    Returns
    -------
    PaperInfo
        解析結果

    Example
    -------
    >>> paper = summarize_paper("research_paper.pdf")
    >>> # セクションごとの要約文にアクセス
    >>> for sec in paper.sections:
    ...     print(sec.name, sec.summary_sentences)
    """
    paper = analyze_paper(pdf_path, sentences_per_section, num_keywords)
    if print_report:
        report = generate_report(paper)
        print(report)
    return paper


# ---------------------------------------------------------------------------
# バッチ処理: 複数論文の一括要約
# ---------------------------------------------------------------------------

def summarize_batch(
    pdf_dir: str,
    sentences_per_section: int = 3,
    num_keywords: int = 10,
) -> list[PaperInfo]:
    """
    ディレクトリ内の全PDFファイルを一括要約する。

    Parameters
    ----------
    pdf_dir : str
        PDFファイルが格納されたディレクトリパス
    sentences_per_section : int
        各セクションから抽出する文の数
    num_keywords : int
        抽出するキーワード数

    Returns
    -------
    list[PaperInfo]
        各論文の解析結果リスト
    """
    dir_path = Path(pdf_dir)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"ディレクトリが見つかりません: {pdf_dir}")

    pdf_files = sorted(dir_path.glob("*.pdf"))
    if not pdf_files:
        print(f"PDFファイルが見つかりません: {pdf_dir}")
        return []

    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'#' * 70}")
        print(f"# [{i}/{len(pdf_files)}] {pdf_file.name}")
        print(f"{'#' * 70}")
        try:
            paper = summarize_paper(
                str(pdf_file), sentences_per_section, num_keywords
            )
            results.append(paper)
        except Exception as e:
            print(f"  エラー: {e}")

    return results


def comparison_table(papers: list[PaperInfo]) -> str:
    """
    複数論文の比較テーブルを生成する。

    Parameters
    ----------
    papers : list[PaperInfo]
        比較対象の論文リスト

    Returns
    -------
    str
        比較テーブルの文字列
    """
    if not papers:
        return "(比較対象の論文がありません)"

    lines = []
    lines.append("=" * 70)
    lines.append("論文比較テーブル (Paper Comparison Table)")
    lines.append("=" * 70)
    lines.append("")

    for i, paper in enumerate(papers, 1):
        lines.append(f"--- 論文 {i} ---")
        lines.append(f"  タイトル: {paper.title}")
        lines.append(f"  ページ数: {paper.total_pages}")
        lines.append(f"  キーワード: {', '.join(paper.keywords[:5])}")

        # Abstract の要約があれば表示
        for sec in paper.sections:
            if sec.name == "Abstract" and sec.summary_sentences:
                lines.append(f"  概要: {sec.summary_sentences[0][:200]}...")
                break
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI エントリーポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使い方: python paper_summarizer.py <PDF_PATH> [PDF_PATH2 ...]")
        print("")
        print("例:")
        print("  python paper_summarizer.py paper.pdf")
        print("  python paper_summarizer.py paper1.pdf paper2.pdf paper3.pdf")
        sys.exit(1)

    pdf_paths = sys.argv[1:]

    if len(pdf_paths) == 1:
        summarize_paper(pdf_paths[0])
    else:
        papers = []
        for path in pdf_paths:
            try:
                paper = summarize_paper(path)
                papers.append(paper)
            except Exception as e:
                print(f"エラー ({path}): {e}")

        if len(papers) > 1:
            print(comparison_table(papers))
