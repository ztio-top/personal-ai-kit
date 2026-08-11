#!/usr/bin/env python3
import os
import yaml
import requests
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PEOSDocument:
    filepath: str
    content: str
    metadata: Dict

    @property
    def doc_type(self) -> str: return self.metadata.get('type', 'note')

    @property
    def status(self) -> str: return self.metadata.get('status', 'draft')

class PEOSKnowledgeBase:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.documents: List[PEOSDocument] = []
        if not self.root_dir.exists():
            print(f"❌ 错误: 知识库路径不存在 ({self.root_dir})", file=sys.stderr)
            sys.exit(1)
        self._load_documents()

    def _load_documents(self):
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if not file.endswith('.md'): continue
                filepath = Path(root) / file
                try:
                    text = filepath.read_text(encoding='utf-8')
                    if text.startswith('---'):
                        parts = text.split('---', 2)
                        if len(parts) >= 3:
                            metadata = yaml.safe_load(parts[1]) or {}
                            content = parts[2].strip()
                            self.documents.append(PEOSDocument(str(filepath), content, metadata))
                except Exception:
                    pass

    def filter_docs(self, doc_type: str = None, status: str = None, keyword: str = None) -> List[PEOSDocument]:
        results = []
        for doc in self.documents:
            if doc_type and doc.doc_type != doc_type: continue
            if status and doc.status != status: continue
            if keyword and keyword.lower() not in doc.content.lower(): continue
            results.append(doc)
        return results

def ask_local_llm(prompt: str, context: str, model: str = "qwen2.5:14b") -> str:
    system_msg = "你是一个资深的架构师。请严格使用提供的 Context 回答问题。无可用信息时直接告知。"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{prompt}"}
        ],
        "stream": False,
        "temperature": 0.1
    }
    try:
        response = requests.post("[http://127.0.0.1:11434/api/chat](http://127.0.0.1:11434/api/chat)", json=payload)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        return f"❌ LLM 调用失败: {e}"

def main():
    parser = argparse.ArgumentParser(description="PEOS RAG 检索引擎")
    parser.add_argument("query", help="向本地知识库提问的问题")
    parser.add_argument("-t", "--type", default="runbook", help="过滤的文档类型 (默认: runbook)")
    parser.add_argument("-s", "--status", default="active", help="过滤的文档状态 (默认: active)")
    parser.add_argument("-k", "--keyword", help="必须包含的硬性关键字")
    parser.add_argument("-m", "--model", default="qwen2.5:14b", help="使用的 Ollama 模型")

    args = parser.parse_args()

    kb_dir = os.getenv("PEOS_KNOWLEDGE_DIR")
    if not kb_dir:
        print("❌ 错误: 未设置 PEOS_KNOWLEDGE_DIR 环境变量", file=sys.stderr)
        sys.exit(1)

    print("🔄 正在挂载 PEOS 知识库并执行元数据预过滤...", file=sys.stderr)
    kb = PEOSKnowledgeBase(kb_dir)

    filtered_docs = kb.filter_docs(doc_type=args.type, status=args.status, keyword=args.keyword)

    if not filtered_docs:
        print(f"🚨 未检索到符合条件 (type={args.type}, status={args.status}) 的有效上下文！")
        sys.exit(0)

    print(f"🎯 命中 {len(filtered_docs)} 份高质量资产。正在联络 AI 核心...\n", file=sys.stderr)

    context_blocks = [f"--- 来源: {doc.filepath} ---\n{doc.content}" for doc in filtered_docs]
    answer = ask_local_llm(args.query, "\n\n".join(context_blocks), model=args.model)

    print("🤖 [PEOS AI 诊断结论]：\n" + "="*50)
    print(answer)
    print("="*50)

if __name__ == "__main__":
    main()
