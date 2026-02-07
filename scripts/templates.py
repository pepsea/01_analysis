"""
論文要約テンプレートモジュール

構造化された要約テンプレートを生成する。
Claude Projects に貼り付けて論文要約を依頼する際のプロンプトも提供する。
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class SummaryInfo:
    """要約の基本情報"""
    title: str = ""
    authors: str = ""
    journal: str = ""
    year: str = ""
    doi: str = ""
    filename: str = ""


def generate_summary_template(info: SummaryInfo | None = None) -> str:
    """
    空の要約テンプレート(Markdown)を生成する。

    Args:
        info: 論文の基本情報（あれば自動埋め込み）

    Returns:
        Markdown形式の要約テンプレート
    """
    today = date.today().isoformat()
    title = info.title if info else ""
    authors = info.authors if info else ""
    journal = info.journal if info else ""
    year = info.year if info else ""
    doi = info.doi if info else ""

    template = f"""# {title or "[論文タイトル]"}

| 項目 | 内容 |
|------|------|
| 著者 | {authors or "[著者名]"} |
| 雑誌 | {journal or "[雑誌名]"} |
| 年 | {year or "[出版年]"} |
| DOI | {doi or "[DOI]"} |
| 要約作成日 | {today} |

---

## 一言まとめ

> [この論文を1文で表すと？]

## 背景と課題

- [この研究が行われた背景]
- [解決しようとしている課題]
- [既存研究の限界]

## 手法

- [使用した実験手法・解析手法]
- [対象サンプル・データセット]
- [重要な実験条件]

## 主要な結果

### Figure/Table ごとのポイント

| Figure/Table | 内容 |
|-------------|------|
| Fig.1 | [内容] |
| Fig.2 | [内容] |
| Table 1 | [内容] |

### キーとなる発見

1. [最も重要な発見]
2. [次に重要な発見]
3. [補足的な発見]

## 考察・意義

- [結果の解釈]
- [分野への貢献・インパクト]
- [実用面での意義]

## 限界と今後の展望

- [著者が認めている限界]
- [今後の研究方向]

## 自分メモ

- **自研究との関連**: [自分の研究にどう関係するか]
- **疑問点**: [読んで生じた疑問]
- **フォローアップ**: [追加で読むべき論文や確認事項]

---

*要約作成日: {today}*
"""
    return template


def generate_claude_prompt(extracted_text: str = "") -> str:
    """
    Claude に論文要約を依頼するためのプロンプトを生成する。

    Args:
        extracted_text: PDFから抽出した論文テキスト（オプション）

    Returns:
        Claudeへのプロンプト文字列
    """
    prompt = """以下の科学論文を読んで、構造化された要約を作成してください。

## 要約の形式

以下のMarkdown形式で出力してください:

### 1. 基本情報
タイトル、著者、雑誌名、出版年、DOIを表形式で記載

### 2. 一言まとめ
論文の核心を1文で表現（専門家でない人にもわかるように）

### 3. 背景と課題
- この研究が必要だった理由
- 解決しようとしている問題
- 箇条書き3点以内

### 4. 手法
- 実験や解析の方法を平易に説明
- 専門用語には簡単な注釈をつける

### 5. 主要な結果
- Figure/Tableごとに1行でポイントを記載
- キーとなる発見を重要度順に3つ

### 6. 考察・意義
- 結果が何を意味するか
- 分野にとってのインパクト

### 7. 限界と今後
- 著者が認めている限界
- 今後の研究方向

### 8. 自分メモ欄（空欄で残す）
- 自研究との関連:
- 疑問点:
- フォローアップ:

## 注意点
- 専門用語は初出時に（ ）内で簡単に説明する
- 図表の番号は原文に合わせる
- 数値データは具体的に記載する
- iPhoneで読みやすいよう、簡潔に記述する
"""

    if extracted_text:
        prompt += f"\n\n## 論文テキスト\n\n{extracted_text}"

    return prompt


def generate_index_entry(info: SummaryInfo, summary_filename: str) -> str:
    """
    要約インデックス(index.md)用の1行エントリを生成する。

    Args:
        info: 論文の基本情報
        summary_filename: 要約ファイル名

    Returns:
        インデックス用のMarkdown行
    """
    today = date.today().isoformat()
    title = info.title or "[タイトル未設定]"
    authors = info.authors or "[著者不明]"
    year = info.year or "----"

    return f"| {today} | [{title}]({summary_filename}) | {authors} | {year} |"
