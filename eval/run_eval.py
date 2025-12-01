
"""
Q&A Evaluation Script
Tests the RAG system against a curated set of questions
"""

import json
import requests
import sys
from typing import List, Dict

API_BASE_URL = "http://localhost:8000"

def load_eval_set(filepath: str = "eval/qa_eval_set.json") -> List[Dict]:
    """Load evaluation questions"""
    with open(filepath, 'r') as f:
        return json.load(f)

def upload_test_documents() -> List[str]:
    """Upload test PDFs and return document IDs"""
    print("📤 Uploading test documents...")
    
    test_files = [
        "uploads/Sample NDA.pdf",
        "uploads/NDA.pdf"
    ]
    
    files = []
    for filepath in test_files:
        try:
            with open(filepath, 'rb') as f:
                files.append(('files', (filepath.split('/')[-1], f.read(), 'application/pdf')))
        except FileNotFoundError:
            print(f"  Warning: {filepath} not found, skipping...")
    
    if not files:
        print("No test documents found in uploads/")
        return []
    
    response = requests.post(f"{API_BASE_URL}/ingest", files=files)
    
    if response.status_code == 200:
        data = response.json()
        doc_ids = data.get('document_ids', [])
        print(f" Uploaded {len(doc_ids)} documents")
        return doc_ids
    else:
        print(f"Upload failed: {response.status_code}")
        return []

def evaluate_question(question: Dict, document_ids: List[str]) -> Dict:
    """Evaluate a single question"""
    print(f"\n Testing Q{question['id']}: {question['question']}")
    
    
    response = requests.post(
        f"{API_BASE_URL}/ask",
        params={"question": question['question']}
    )
    
    if response.status_code != 200:
        print(f"   API Error: {response.status_code}")
        return {
            "question_id": question['id'],
            "score": 0.0,
            "reason": f"API error: {response.status_code}"
        }
    
    data = response.json()
    answer = data.get('answer', '').lower()
    
   
    score = 0.0
    matched_keywords = []
    
   
    for keyword in question['expected_keywords']:
        if keyword.lower() in answer:
            matched_keywords.append(keyword)
    
   
    if len(question['expected_keywords']) > 0:
        score = len(matched_keywords) / len(question['expected_keywords'])
    
    
    negative_phrases = ["not found", "cannot find", "no information", "not in the document"]
    has_negative = any(phrase in answer for phrase in negative_phrases)
    
    if has_negative:
        score *= 0.5  
    
   
    has_citations = len(data.get('citations', [])) > 0
    if has_citations:
        score += 0.1  
    
    score = min(score, 1.0)  
    
    
    status = "✅" if score >= 0.7 else "⚠️" if score >= 0.4 else "❌"
    print(f"   {status} Score: {score:.2f}")
    print(f"   Matched keywords: {matched_keywords}")
    if has_citations:
        print(f"   📚 Has citations")
    
    return {
        "question_id": question['id'],
        "question": question['question'],
        "answer": data.get('answer', ''),
        "score": score,
        "matched_keywords": matched_keywords,
        "has_citations": has_citations
    }

def run_evaluation():
    """Run full evaluation"""
    print("=" * 60)
    print("🧪 Contract Intelligence API - Q&A Evaluation")
    print("=" * 60)
    
   
    try:
        health = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health.status_code != 200:
            print("API is not healthy. Please start the API first:")
            print("   docker-compose up")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start it first:")
        print("   docker-compose up")
        sys.exit(1)
    
    
    doc_ids = upload_test_documents()
    if not doc_ids:
        print("❌ No documents uploaded. Evaluation cannot proceed.")
        sys.exit(1)
    
    
    eval_set = load_eval_set()
    print(f"\n📋 Loaded {len(eval_set)} test questions\n")
    
   
    results = []
    for question in eval_set:
        result = evaluate_question(question, doc_ids)
        results.append(result)
    
    
    avg_score = sum(r['score'] for r in results) / len(results)
    
   
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Questions: {len(results)}")
    print(f"Average Score: {avg_score:.2f}")
    print(f"Pass Rate (≥0.7): {sum(1 for r in results if r['score'] >= 0.7)}/{len(results)}")
    
    
    if avg_score >= 0.8:
        grade = "🌟 EXCELLENT"
    elif avg_score >= 0.7:
        grade = "✅ GOOD"
    elif avg_score >= 0.5:
        grade = "⚠️  FAIR"
    else:
        grade = "❌ NEEDS IMPROVEMENT"
    
    print(f"\nOverall Grade: {grade}")
    
    
    with open('eval/eval_results.json', 'w') as f:
        json.dump({
            "average_score": avg_score,
            "total_questions": len(results),
            "pass_rate": sum(1 for r in results if r['score'] >= 0.7) / len(results),
            "results": results
        }, f, indent=2)
    
    print("\n💾 Detailed results saved to: eval/eval_results.json")
    
    
    print("\n" + "=" * 60)
    print("📝 ONE-LINE SUMMARY (for submission):")
    print("=" * 60)
    print(f"Q&A Accuracy: {avg_score:.1%} ({sum(1 for r in results if r['score'] >= 0.7)}/{len(results)} passed) - {grade}")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()