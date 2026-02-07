#!/usr/bin/env python3
"""
科学論文要約システム - メインスクリプト

使い方:
  1. テキスト抽出 + テンプレート生成:
     python scripts/summarize_paper.py papers/sample.pdf

  2. Claude用プロンプト生成(コピペ用):
     python scripts/summarize_paper.py papers/sample.pdf --prompt

  3. 空テンプレートだけ生成:
     python scripts/summarize_paper.py --template

ワークフロー:
  Step 1: このスクリプトでPDFからテキスト抽出 & プロンプト生成
  Step 2: Claude Projects に PDF をアップロード
  Step 3: 生成されたプロンプトを Claude に貼り付けて要約依頼
  Step 4: Claude の出力を summaries/ に保存
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# スクリプトディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from pdf_extractor import extract_text_from_pdf, paper_to_text, ExtractedPaper
from templates import (
    SummaryInfo,
    generate_summary_template,
    generate_claude_prompt,
    generate_index_entry,
)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
SUMMARIES_DIR = PROJECT_ROOT / "summaries"
PAPERS_DIR = PROJECT_ROOT / "papers"


def make_summary_filename(paper: ExtractedPaper) -> str:
    """論文情報からファイル名を生成"""
    today = date.today().isoformat()
    title = paper.metadata.title or "untitled"
    # ファイル名に使えない文字を除去
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = re.sub(r'\s+', '_', safe_title.strip())
    safe_title = safe_title[:60]  # 長すぎる場合は切り詰め
    return f"{today}_{safe_title}.md"


def extract_and_show(pdf_path: str) -> ExtractedPaper:
    """PDFを抽出して結果を表示"""
    print(f"📄 PDFを読み込み中: {pdf_path}")
    paper = extract_text_from_pdf(pdf_path)

    meta = paper.metadata
    print(f"\n{'='*50}")
    print(f"抽出完了!")
    print(f"{'='*50}")
    print(f"  タイトル:   {meta.title or '(不明)'}")
    print(f"  著者:       {meta.authors or '(不明)'}")
    print(f"  年:         {meta.year or '(不明)'}")
    print(f"  DOI:        {meta.doi or '(不明)'}")
    print(f"  ページ数:   {meta.pages}")
    print(f"  テキスト長: {len(paper.full_text):,}文字")

    if paper.sections:
        print(f"\n  検出セクション:")
        for name in paper.sections:
            print(f"    - {name}")

    return paper


def save_extracted_text(paper: ExtractedPaper, output_path: Path):
    """抽出テキストをファイルに保存"""
    text = paper_to_text(paper)
    output_path.write_text(text, encoding="utf-8")
    print(f"\n✅ 抽出テキスト保存: {output_path}")


def save_prompt(paper: ExtractedPaper, output_path: Path):
    """Claude用プロンプトをファイルに保存"""
    text = paper_to_text(paper)
    prompt = generate_claude_prompt(text)
    output_path.write_text(prompt, encoding="utf-8")
    print(f"✅ Claudeプロンプト保存: {output_path}")


def save_template(paper: ExtractedPaper | None, output_path: Path):
    """要約テンプレートをファイルに保存"""
    info = None
    if paper:
        info = SummaryInfo(
            title=paper.metadata.title,
            authors=paper.metadata.authors,
            journal=paper.metadata.journal,
            year=paper.metadata.year,
            doi=paper.metadata.doi,
            filename=paper.metadata.filename,
        )
    template = generate_summary_template(info)
    output_path.write_text(template, encoding="utf-8")
    print(f"✅ 要約テンプレート保存: {output_path}")


def update_index(paper: ExtractedPaper, summary_filename: str):
    """要約インデックスを更新"""
    index_path = SUMMARIES_DIR / "index.md"
    info = SummaryInfo(
        title=paper.metadata.title,
        authors=paper.metadata.authors,
        year=paper.metadata.year,
    )
    entry = generate_index_entry(info, summary_filename)

    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        content = content.rstrip() + "\n" + entry + "\n"
    else:
        content = "# 論文要約インデックス\n\n"
        content += "| 日付 | タイトル | 著者 | 年 |\n"
        content += "|------|---------|------|----|\n"
        content += entry + "\n"

    index_path.write_text(content, encoding="utf-8")
    print(f"✅ インデックス更新: {index_path}")


def cmd_process(args):
    """PDFを処理してすべての出力を生成"""
    paper = extract_and_show(args.pdf)
    SUMMARIES_DIR.mkdir(exist_ok=True)

    summary_filename = make_summary_filename(paper)

    # 抽出テキスト保存
    extracted_path = SUMMARIES_DIR / summary_filename.replace(".md", "_extracted.txt")
    save_extracted_text(paper, extracted_path)

    if args.prompt:
        # Claude用プロンプト生成
        prompt_path = SUMMARIES_DIR / summary_filename.replace(".md", "_prompt.txt")
        save_prompt(paper, prompt_path)

    # 要約テンプレート保存
    template_path = SUMMARIES_DIR / summary_filename
    save_template(paper, template_path)

    # インデックス更新
    update_index(paper, summary_filename)

    print(f"\n{'='*50}")
    print("次のステップ:")
    print(f"{'='*50}")
    print()
    print("1. Claude Projects にPDFをアップロード:")
    print(f"   {args.pdf}")
    print()
    if args.prompt:
        prompt_path = SUMMARIES_DIR / summary_filename.replace(".md", "_prompt.txt")
        print("2. 以下のプロンプトファイルの内容をClaudeに貼り付け:")
        print(f"   {prompt_path}")
    else:
        print("2. Claudeに以下のように依頼:")
        print("   「この論文を構造化して要約してください」")
    print()
    print("3. Claudeの出力で要約テンプレートを更新:")
    print(f"   {template_path}")
    print()
    print("💡 iPhoneのClaudeアプリから同じProjectにアクセスして")
    print("   いつでも要約を確認・質問できます")


def cmd_template(args):
    """空テンプレートだけ生成"""
    SUMMARIES_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    output_path = SUMMARIES_DIR / f"{today}_template.md"
    save_template(None, output_path)


def cmd_prompt(args):
    """プロンプトだけ表示"""
    prompt = generate_claude_prompt()
    print(prompt)


def main():
    parser = argparse.ArgumentParser(
        description="科学論文要約システム - PDFからClaudeで要約を作成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # PDFを処理（テキスト抽出 + テンプレート生成）
  python scripts/summarize_paper.py papers/sample.pdf

  # Claude用プロンプトも同時生成
  python scripts/summarize_paper.py papers/sample.pdf --prompt

  # 空テンプレートだけ生成
  python scripts/summarize_paper.py --template

  # プロンプトだけ表示
  python scripts/summarize_paper.py --show-prompt
        """,
    )

    parser.add_argument(
        "pdf",
        nargs="?",
        help="論文PDFファイルのパス",
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="Claude用プロンプトファイルも生成する",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="空の要約テンプレートだけ生成する",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Claude用の汎用プロンプトを表示する",
    )

    args = parser.parse_args()

    if args.show_prompt:
        cmd_prompt(args)
    elif args.template:
        cmd_template(args)
    elif args.pdf:
        cmd_process(args)
    else:
        parser.print_help()
        print("\nエラー: PDFファイルを指定するか、--template / --show-prompt を使用してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
