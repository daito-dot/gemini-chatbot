"""Gemini チャットボット - Streamlit アプリケーション"""

import os
from pathlib import Path

import streamlit as st

from src.chat import GeminiChat
from src.document_loader import DocumentLoader

# 事前登録ドキュメントのディレクトリ
DOCS_DIR = Path(__file__).parent / "docs"

# ページ設定
st.set_page_config(
    page_title="Gemini チャットボット",
    page_icon="🤖",
    layout="wide",
)


def load_preset_documents(chat: GeminiChat, loader: DocumentLoader):
    """docs/ フォルダから事前登録ドキュメントを読み込み"""
    if not DOCS_DIR.exists():
        return

    supported_extensions = {".pdf", ".txt", ".md", ".csv"}

    for file_path in DOCS_DIR.iterdir():
        if file_path.suffix.lower() in supported_extensions:
            if file_path.name not in chat.get_document_list():
                try:
                    with open(file_path, "rb") as f:
                        content = loader.load(f.read(), file_path.name)
                    chat.add_document(f"[preset] {file_path.name}", content)
                except Exception:
                    pass  # 読み込み失敗は無視


def init_session_state():
    """セッション状態の初期化"""
    if "chat" not in st.session_state:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            st.session_state.chat = GeminiChat(api_key)
        else:
            st.session_state.chat = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "loader" not in st.session_state:
        st.session_state.loader = DocumentLoader()

    # 事前登録ドキュメントを読み込み
    if "preset_loaded" not in st.session_state and st.session_state.chat:
        load_preset_documents(st.session_state.chat, st.session_state.loader)
        st.session_state.preset_loaded = True


def main():
    """メイン処理"""
    init_session_state()

    # サイドバー
    with st.sidebar:
        st.header("📁 ドキュメント管理")

        # API キーの確認
        if st.session_state.chat is None:
            st.error("⚠️ GEMINI_API_KEY が設定されていません")
            st.info("`.streamlit/secrets.toml` に API キーを設定してください")
            api_key_input = st.text_input("API キーを入力:", type="password")
            if api_key_input:
                st.session_state.chat = GeminiChat(api_key_input)
                st.rerun()
            return

        # ファイルアップロード
        uploaded_files = st.file_uploader(
            "ファイルをアップロード",
            type=["pdf", "txt", "md", "csv"],
            accept_multiple_files=True,
            help="PDF, テキスト, Markdown, CSV に対応",
        )

        # アップロードされたファイルを処理
        if uploaded_files:
            for file in uploaded_files:
                if file.name not in st.session_state.chat.get_document_list():
                    try:
                        content = st.session_state.loader.load(
                            file.read(), file.name
                        )
                        st.session_state.chat.add_document(file.name, content)
                        st.success(f"✅ {file.name}")
                    except Exception as e:
                        st.error(f"❌ {file.name}: {e}")

        st.divider()

        # URL入力
        url_input = st.text_input(
            "URLを追加:",
            placeholder="https://example.com",
            help="Webページの内容を取得します",
        )

        if st.button("URLを追加", disabled=not url_input):
            if url_input:
                try:
                    content = st.session_state.loader.load(url_input)
                    # URLを短縮してファイル名として使用
                    short_name = url_input[:50] + "..." if len(url_input) > 50 else url_input
                    st.session_state.chat.add_document(short_name, content)
                    st.success(f"✅ URLを追加しました")
                except Exception as e:
                    st.error(f"❌ 取得失敗: {e}")

        st.divider()

        # 登録済みドキュメント一覧
        docs = st.session_state.chat.get_document_list()
        if docs:
            st.subheader("📄 登録済みドキュメント")
            for doc in docs:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(doc[:30] + "..." if len(doc) > 30 else doc)
                with col2:
                    if st.button("🗑️", key=f"del_{doc}"):
                        st.session_state.chat.remove_document(doc)
                        st.rerun()

            if st.button("全てクリア", type="secondary"):
                st.session_state.chat.clear_documents()
                st.session_state.messages = []
                st.rerun()
        else:
            st.info("ドキュメントをアップロードしてください")

    # メインエリア
    st.title("🤖 Gemini チャットボット")
    st.caption("アップロードしたドキュメントについて質問できます")

    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザー入力
    if prompt := st.chat_input("質問を入力してください..."):
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # アシスタントの回答を生成
        with st.chat_message("assistant"):
            with st.spinner("考え中..."):
                response = st.session_state.chat.generate(prompt)
                st.markdown(response)

        # アシスタントメッセージを追加
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
