# 01_analysis

ペプチド配列解析と科学論文要約のためのツール群。

## 科学論文要約システム

PDFの科学論文を構造化して要約し、Claude Projects 経由で iPhone からも閲覧できる仕組み。

### セットアップ

```bash
pip install pymupdf
```

### 使い方

#### Step 1: PDFからテキスト抽出 & テンプレート生成

```bash
# 基本（テキスト抽出 + 要約テンプレート生成）
python scripts/summarize_paper.py papers/論文.pdf

# Claude用プロンプトも同時生成
python scripts/summarize_paper.py papers/論文.pdf --prompt
```

#### Step 2: Claude Projects で要約作成

1. [claude.ai](https://claude.ai) で Project を作成（例: 「論文要約」）
2. 論文PDFを Project にアップロード
3. 生成されたプロンプト(`summaries/*_prompt.txt`)の内容を貼り付け
4. Claude が構造化された要約を生成

#### Step 3: iPhoneで閲覧

1. iPhone の Claude アプリを開く
2. 同じ Project にアクセス
3. 要約を確認、追加質問も可能

### その他のコマンド

```bash
# 空の要約テンプレートだけ作成
python scripts/summarize_paper.py --template

# Claude用プロンプトを確認
python scripts/summarize_paper.py --show-prompt
```

### ディレクトリ構成

```
papers/          # 論文PDF置き場
summaries/       # 生成された要約・テンプレート
  index.md       # 要約一覧
scripts/         # ツールスクリプト
  summarize_paper.py  # メインスクリプト
  pdf_extractor.py    # PDFテキスト抽出
  templates.py        # 要約テンプレート
```