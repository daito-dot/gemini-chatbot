"""ドキュメント読み込みモジュール"""

import csv
import io
from pathlib import Path
from typing import Union

import pandas as pd
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader


class DocumentLoader:
    """各種ドキュメント形式からテキストを抽出するクラス"""

    def load(self, source: Union[str, bytes], filename: str = "") -> str:
        """
        ファイルまたはURLからテキストを抽出

        Args:
            source: ファイルパス、URL、またはバイトデータ
            filename: バイトデータの場合のファイル名（拡張子判定用）

        Returns:
            抽出されたテキスト
        """
        # URLの場合
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            return self._load_web(source)

        # バイトデータの場合（Streamlitのアップロード）
        if isinstance(source, bytes):
            ext = Path(filename).suffix.lower()
            return self._load_bytes(source, ext)

        # ファイルパスの場合
        if isinstance(source, str):
            ext = Path(source).suffix.lower()
            return self._load_file(source, ext)

        raise ValueError(f"Unsupported source type: {type(source)}")

    def _load_file(self, path: str, ext: str) -> str:
        """ファイルパスから読み込み"""
        with open(path, "rb") as f:
            return self._load_bytes(f.read(), ext)

    def _load_bytes(self, data: bytes, ext: str) -> str:
        """バイトデータから読み込み"""
        loaders = {
            ".pdf": self._load_pdf,
            ".txt": self._load_text,
            ".md": self._load_text,
            ".csv": self._load_csv,
        }

        loader = loaders.get(ext)
        if not loader:
            raise ValueError(f"Unsupported file type: {ext}")

        return loader(data)

    def _load_pdf(self, data: bytes) -> str:
        """PDFからテキスト抽出"""
        reader = PdfReader(io.BytesIO(data))
        texts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n".join(texts)

    def _load_text(self, data: bytes) -> str:
        """テキスト/Markdownファイルを読み込み"""
        # UTF-8を試し、失敗したらcp932（日本語Windows）を試す
        for encoding in ["utf-8", "cp932", "shift_jis"]:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="ignore")

    def _load_csv(self, data: bytes) -> str:
        """CSVをテキストとして読み込み"""
        text = self._load_text(data)
        df = pd.read_csv(io.StringIO(text))
        # DataFrameを読みやすい形式に変換
        return df.to_markdown(index=False)

    def _load_web(self, url: str) -> str:
        """WebページからテキストG抽出"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 不要な要素を削除
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # テキストを抽出
        text = soup.get_text(separator="\n", strip=True)

        # 空行を整理
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)
