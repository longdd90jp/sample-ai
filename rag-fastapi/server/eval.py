# eval.py
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

judge = ChatOpenAI(model="gpt-4o", temperature=0)

def judge_pair(question, answer, ref):
    prompt = f"""You are a strict evaluator.
Q: {question}
Candidate: {answer}
Reference: {ref}
Score 1-5 for factuality & completeness. Return JSON {{"factuality":int,"completeness":int}}."""
    res = judge.predict_messages([HumanMessage(content=prompt)])
    try:
        return json.loads(res.content)
    except Exception:
        return {"factuality": 3, "completeness": 3}