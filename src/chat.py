"""Gemini チャットモジュール"""

import google.generativeai as genai


class GeminiChat:
    """Gemini APIを使用したチャットクラス"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        初期化

        Args:
            api_key: Gemini API キー
            model_name: 使用するモデル名
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.documents: dict[str, str] = {}  # filename -> content

    def add_document(self, filename: str, content: str) -> None:
        """
        ドキュメントを追加

        Args:
            filename: ファイル名
            content: ドキュメントの内容
        """
        self.documents[filename] = content

    def remove_document(self, filename: str) -> None:
        """ドキュメントを削除"""
        if filename in self.documents:
            del self.documents[filename]

    def clear_documents(self) -> None:
        """全ドキュメントをクリア"""
        self.documents.clear()

    def get_document_list(self) -> list[str]:
        """ドキュメント一覧を取得"""
        return list(self.documents.keys())

    def generate(self, query: str) -> str:
        """
        ユーザーの質問に回答を生成

        Args:
            query: ユーザーの質問

        Returns:
            生成された回答
        """
        if not self.documents:
            return "ドキュメントがアップロードされていません。サイドバーからファイルをアップロードしてください。"

        # コンテキストを構築
        context_parts = []
        for filename, content in self.documents.items():
            context_parts.append(f"=== {filename} ===\n{content}")

        context = "\n\n".join(context_parts)

        # プロンプトを構築
        prompt = f"""あなたは親切で知識豊富なアシスタントです。
以下のドキュメントの内容を参考に、ユーザーの質問に日本語で回答してください。

## ルール
- ドキュメントの内容に基づいて正確に回答してください
- ドキュメントに情報がない場合は、その旨を伝えてください
- 回答は分かりやすく、簡潔にしてください
- 必要に応じて箇条書きや見出しを使ってください

## ドキュメント
{context}

## ユーザーの質問
{query}

## 回答"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"
