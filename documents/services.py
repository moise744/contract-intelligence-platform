import os
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessingService:
    @staticmethod
    def extract_text_from_pdf(file_path):
        """Extracts text from a given PDF file."""
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
        return text

    @staticmethod
    def chunk_text(text, chunk_size=1000, chunk_overlap=200):
        """Chunks text using LangChain's RecursiveCharacterTextSplitter."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)
        return chunks
