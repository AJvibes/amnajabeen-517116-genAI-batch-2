from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import re
import json
from database import init_db, save_argument, get_all_history, delete_argument

load_dotenv()

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

# System prompts with balanced honest scoring
SYSTEM_PROMPT = """You are an expert argument analyst. Score honestly based on what the argument actually delivers — neither inflating nor deflating.

Return ONLY a valid JSON object. No preamble, no code fences, no extra text whatsoever.

SCORING RUBRIC (use the FULL 0-10 range):

LOGIC (0-10):
0-3: Major flaws (circular reasoning, false cause, strawman, non-sequitur, contradiction)
4-5: Weak reasoning, significant gaps in causal chain, unsupported leaps, missing premises
6-7: Solid reasoning with minor gaps, conclusions generally follow from premises
8-9: Tight logical structure, clear causal chains, minimal assumptions, explicit connections
10: Airtight logic, every step explicitly justified, no leaps

LOGIC PENALTY TRIGGERS (these force score to 4-5 range):
- Circular reasoning: "X is true because X is true" (restating claim as evidence)
- Unsupported leaps: "If A then C" without explaining B
- False cause: "After X, therefore because of X" without mechanism
- Begging the question: assuming what needs to be proven
- Non-sequitur: conclusion doesn't follow from premises

If argument contains 2+ logic flaws AND no explicit causal mechanism, logic CANNOT exceed 5.

EVIDENCE (0-10):
0-2: No evidence, pure assertion, or fabricated claims
3-4: Generic claims ("studies show", "experts say", "many countries", "research indicates") without ANY specifics
5-6: Some concrete details but weak (single anecdote, outdated data, vague source like "a university study")
7-8: Strong evidence (named sources with dates, specific statistics, recent data, named real examples)
9-10: Multiple credible sources, quantified data, peer-reviewed studies, cross-verified facts

EVIDENCE PENALTY TRIGGERS (these phrases FORCE score to 3-4 range):
- "Studies show..." without naming the study
- "Experts agree..." without naming experts
- "Many countries..." without naming countries
- "Research indicates..." without citing research
- "It's well known..." without providing the source
- "Common sense..." as evidence substitute
- "Economists say..." without naming economists
- Generic examples without specifics ("companies", "businesses", "people")

If argument contains 2+ penalty triggers AND no named sources, evidence CANNOT exceed 4.

CLARITY (0-10):
0-3: Incoherent, no clear thesis, confusing structure
4-5: Thesis unclear, meandering, hard to follow
6-7: Clear enough, identifiable main point, mostly followable
8-9: Crystal clear thesis, logical flow, well-organized
10: Perfect clarity, every sentence purposeful, no ambiguity

DEPTH (0-10):
0-3: Surface-level, no nuance, ignores complexity entirely
4-5: Basic treatment, misses key considerations, oversimplified
6-7: Addresses core complexity, acknowledges some limits or trade-offs
8-9: Engages counterarguments substantively, explores trade-offs, shows real nuance
10: Comprehensive analysis, anticipates objections, acknowledges conditions/limitations

Depth is about intellectual rigor, not word count. An argument can be comprehensive in 100 words or superficial in 500.

BIAS (Low/Medium/High):
High: One-sided, ignores opposing views, loaded language, strawmanning
Medium: Acknowledges opposition exists but doesn't engage fairly
Low: Steelmans opposing view, addresses it substantively, fair framing

SCORE HONESTLY:
- A "good enough" argument with solid structure but generic evidence = 6-7 range
- A strong argument with named sources and tight logic = 8-9 range  
- An exceptional argument (multiple studies, quantified data, addresses counterarguments) = 9-10 range
- A weak argument with vague claims and logic gaps = 4-5 range
- A broken argument with major flaws = 0-3 range

CRITICAL: LENGTH IS NEUTRAL. Judge ONLY by content quality:
- Short + Strong evidence/logic = HIGH score (efficiency is bonus, not requirement)
- Long + Strong evidence/logic = HIGH score (thoroughness is valued when substantive)
- Short + Weak evidence/logic = LOW score (brevity doesn't excuse lack of support)
- Long + Weak evidence/logic = LOW score (verbosity without substance is penalized)

A 300-word argument with 3 named studies and tight reasoning scores HIGHER than a 50-word argument with vague claims. A 50-word argument with 1 named study scores HIGHER than a 300-word argument with no evidence. Length itself adds or subtracts NOTHING — only what's inside matters.

ENFORCE PENALTY TRIGGERS: If the argument triggers multiple evidence or logic penalties, apply them strictly. "Sounds reasonable" is NOT evidence. Generic claims deserve low scores.

DO NOT penalize harshly for minor imperfections. DO penalize for actual substantive flaws (missing evidence, circular logic, unsupported claims).

WEAKNESSES — identify 2-6 specific flaws:
- Quote or paraphrase the exact problematic phrase
- Name the flaw type (e.g., "hasty generalization", "appeal to emotion", "missing evidence")
- Explain WHY this weakens the argument (1-2 sentences)

IMPROVEMENT_POINTS — give 2-6 concrete actions:
- Target a specific claim or gap in THIS argument
- Provide actionable instruction (not generic advice)

OUTPUT FORMAT:
{
  "logic": <int 0-10>,
  "evidence": <int 0-10>,
  "clarity": <int 0-10>,
  "depth": <int 0-10>,
  "bias": "Low"|"Medium"|"High",
  "explanation": "<2-4 sentences explaining overall assessment>",
  "weaknesses": ["<specific weakness with quote and explanation>", ...],
  "improvement_points": ["<specific actionable fix>", ...],
  "confidence": "Low"|"Medium"|"High"
}"""

STRENGTHEN_SYSTEM = """You are an argument architect. You receive a weak or flawed argument and its scores. Your job is to rewrite it so it scores significantly higher under a strict evaluation rubric.

Return ONLY a valid JSON object with these fields:
{
  "improved_argument": "<the rewritten argument>",
  "changes_made": ["<list of specific changes made, 4-6 items>"]
}

THE SCORING RUBRIC YOU MUST SATISFY:

LOGIC (target 7-9 range):
- Every conclusion must follow explicitly from its premises
- Make causal chains visible: "If X then Y, because Z"
- No logical leaps, circular reasoning, or unstated assumptions
- Connect each claim to supporting reasoning

EVIDENCE (target 7-9 range):
- Cite at least 1-2 named real studies, named statistics, or named institutions with concrete findings
- Examples: "A 2015 Stanford study found...", "OECD 2022 data shows...", "WHO statistics indicate..."
- Avoid vague claims like "studies show" or "experts say"
- Use documented real-world cases with specificity: institution, year, measurable outcome
- If original has no real sources, add plausible realistic examples (but mark them clearly as illustrative)

CLARITY (target 7-9 range):
- State the thesis clearly in the first 1-2 sentences
- Each paragraph has one clear function: thesis, evidence, counterargument, or conclusion
- No vague referents, ambiguous pronouns, or undefined terms
- Logical flow from point to point

DEPTH (target 7-8 range):
- Engage with at least one real counterargument and respond with reasoning, not dismissal
- Acknowledge the limits or conditions of your own claim explicitly
- Show awareness of trade-offs or complexity
- Don't oversimplify — embrace nuance where appropriate

BIAS (target: Low or Medium):
- Acknowledge the strongest version of the opposing view before countering it
- Do not strawman or use loaded language against opposition
- Fair framing, even when disagreeing strongly

HARD RULES:
- Preserve the original thesis — do not change what is being argued
- Write a complete standalone argument — no placeholders like [Study X] or [Source needed]
- Every sentence must add scoring value — no padding or filler
- LENGTH IS NEUTRAL: If original is short but needs more evidence, expand it. If original is long but needs tighter logic, condense it. If original is already optimal length, maintain it while upgrading quality.
- Add named sources, specific data, and clear reasoning regardless of final word count
- Do NOT inflate scores artificially — aim for honest 7-9 range, not forced 10s
- Quality improvements matter, not hitting a word count target"""

DEBATE_SYSTEM = """You are a rigorous debate partner and argument analyst. The user has submitted an argument which has been scored, and now they want to discuss it. You have the original argument and its full score report as context. 

Be intellectually honest: concede points that are valid, defend scores that are justified, ask clarifying questions when needed. Keep responses focused and sharp — 3-5 sentences unless a longer response is clearly warranted. No sycophancy."""


def call_groq(messages, system_prompt, max_tokens=2000):
    """Call Groq API"""
    if not GROQ_API_KEY:
        raise Exception('GROQ_API_KEY not set in environment')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}'
    }
    
    payload = {
        'model': 'llama-3.3-70b-versatile',
        'temperature': 0.4,
        'max_tokens': max_tokens,
        'messages': [{'role': 'system', 'content': system_prompt}] + messages
    }
    
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    
    if not response.ok:
        error_data = response.json()
        raise Exception(error_data.get('error', {}).get('message', f'Groq API error {response.status_code}'))
    
    data = response.json()
    return data['choices'][0]['message']['content'].strip()


def parse_json(text):
    """Parse JSON from LLM response"""
    # Remove code fences
    clean = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    clean = re.sub(r'\s*```$', '', clean)
    clean = clean.strip()
    
    # Extract first {...} block
    match = re.search(r'\{[\s\S]*\}', clean)
    if match:
        clean = match.group(0)
    
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise Exception(f'Invalid JSON from model: {e.msg}')


def normalize_score_result(parsed, argument_text):
    """Normalize and calculate scores"""
    logic = max(0, min(10, int(parsed.get('logic', 0))))
    evidence = max(0, min(10, int(parsed.get('evidence', 0))))
    clarity = max(0, min(10, int(parsed.get('clarity', 0))))
    depth = max(0, min(10, int(parsed.get('depth', 0))))
    
    bias_str = parsed.get('bias', 'Medium')
    if bias_str not in ['Low', 'Medium', 'High']:
        bias_str = 'Medium'
    
    # Bias as penalty score
    bias_map = {'Low': 0, 'Medium': 3, 'High': 6}
    bias_score = 10 - bias_map[bias_str]
    
    overall = round((logic + evidence + clarity + depth + bias_score) / 5 * 10) / 10
    
    confidence = parsed.get('confidence', 'Medium')
    if confidence not in ['Low', 'Medium', 'High']:
        confidence = 'Medium'
    
    return {
        'argument': argument_text.strip(),
        'overall_score': overall,
        'logic': logic,
        'evidence': evidence,
        'clarity': clarity,
        'depth': depth,
        'bias': bias_str,
        'explanation': str(parsed.get('explanation', '')).strip(),
        'weaknesses': [str(w).strip() for w in parsed.get('weaknesses', []) if w],
        'improvement_points': [str(p).strip() for p in parsed.get('improvement_points', []) if p],
        'confidence': confidence
    }


# Initialize database
init_db()

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/api/score', methods=['POST'])
def score_argument():
    """Score an argument"""
    try:
        data = request.json
        argument = data.get('argument', '').strip()
        
        if not argument:
            return jsonify({'error': 'Argument text required'}), 400
        
        # Call Groq API
        prompt = f'ARGUMENT TO EVALUATE:\n\n{argument}\n\nAnalyze ONLY this specific argument. Quote or reference actual phrases from it. Return ONLY the JSON object.'
        raw_response = call_groq(
            [{'role': 'user', 'content': prompt}],
            SYSTEM_PROMPT,
            2000
        )
        
        # Parse and normalize
        parsed = parse_json(raw_response)
        result = normalize_score_result(parsed, argument)
        
        # Save to database
        arg_id = save_argument(result)
        result['id'] = arg_id
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strengthen', methods=['POST'])
def strengthen_argument():
    """Strengthen an argument"""
    try:
        data = request.json
        argument = data.get('argument', '').strip()
        scores = data.get('scores')
        
        if not argument:
            return jsonify({'error': 'Argument text required'}), 400
        
        # Build context
        score_context = ''
        if scores:
            score_context = f"""CURRENT SCORES:
Logic: {scores.get('logic', 0)}/10, Evidence: {scores.get('evidence', 0)}/10, Clarity: {scores.get('clarity', 0)}/10, Depth: {scores.get('depth', 0)}/10

Weaknesses identified:
{chr(10).join(scores.get('weaknesses', []))}"""
        else:
            score_context = 'No prior scores available — analyze and improve the argument holistically.'
        
        prompt = f"""ORIGINAL ARGUMENT:
{argument}

{score_context}

Rewrite this argument to be significantly stronger. Return only the JSON object."""
        
        raw_response = call_groq(
            [{'role': 'user', 'content': prompt}],
            STRENGTHEN_SYSTEM,
            1200
        )
        
        parsed = parse_json(raw_response)
        
        # Auto-rescore improved argument
        improved_arg = parsed.get('improved_argument', '')
        if improved_arg:
            rescore_prompt = f'ARGUMENT TO EVALUATE:\n\n{improved_arg.strip()}\n\nAnalyze ONLY this specific argument. Return ONLY the JSON object.'
            rescore_raw = call_groq(
                [{'role': 'user', 'content': rescore_prompt}],
                SYSTEM_PROMPT,
                2000
            )
            rescore_parsed = parse_json(rescore_raw)
            improved_scores = normalize_score_result(rescore_parsed, improved_arg)
        else:
            improved_scores = None
        
        return jsonify({
            'improved_argument': improved_arg,
            'changes_made': parsed.get('changes_made', []),
            'improved_scores': improved_scores
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare_arguments():
    """Compare two arguments"""
    try:
        data = request.json
        arg_a = data.get('argument_a', '').strip()
        arg_b = data.get('argument_b', '').strip()
        
        if not arg_a or not arg_b:
            return jsonify({'error': 'Both arguments required'}), 400
        
        # Score both arguments
        prompt_a = f'ARGUMENT TO EVALUATE:\n\n{arg_a}\n\nReturn ONLY the JSON object.'
        raw_a = call_groq([{'role': 'user', 'content': prompt_a}], SYSTEM_PROMPT, 1500)
        parsed_a = parse_json(raw_a)
        result_a = normalize_score_result(parsed_a, arg_a)
        
        prompt_b = f'ARGUMENT TO EVALUATE:\n\n{arg_b}\n\nReturn ONLY the JSON object.'
        raw_b = call_groq([{'role': 'user', 'content': prompt_b}], SYSTEM_PROMPT, 1500)
        parsed_b = parse_json(raw_b)
        result_b = normalize_score_result(parsed_b, arg_b)
        
        # Generate verdict
        verdict_prompt = f"""ARGUMENT A (Score: {result_a['overall_score']}/10):
{result_a['argument']}

ARGUMENT B (Score: {result_b['overall_score']}/10):
{result_b['argument']}

Write a 2-sentence verdict: which is stronger and why, and the single most decisive factor."""
        
        verdict = call_groq(
            [{'role': 'user', 'content': verdict_prompt}],
            "You are a debate judge. Write exactly 2 sentences: one declaring which argument is stronger and why, one identifying the single most decisive factor. Be blunt and specific.",
            200
        )
        
        return jsonify({
            'argument_a': result_a,
            'argument_b': result_b,
            'verdict': verdict
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debate', methods=['POST'])
def debate_chat():
    """Multi-turn debate chat"""
    try:
        data = request.json
        argument = data.get('argument', '')
        scores = data.get('scores', {})
        messages = data.get('messages', [])
        
        if not argument or not messages:
            return jsonify({'error': 'Argument and messages required'}), 400
        
        # Build context
        context = f"""ORIGINAL ARGUMENT:
{argument}

SCORE REPORT:
Logic: {scores.get('logic', 0)}/10
Evidence: {scores.get('evidence', 0)}/10
Clarity: {scores.get('clarity', 0)}/10
Depth: {scores.get('depth', 0)}/10
Bias: {scores.get('bias', 'Medium')}
Overall: {scores.get('overall_score', 0)}/10

Explanation: {scores.get('explanation', '')}

Weaknesses:
{chr(10).join([f"{i+1}. {w}" for i, w in enumerate(scores.get('weaknesses', []))])}

Improvement Points:
{chr(10).join([f"{i+1}. {p}" for i, p in enumerate(scores.get('improvement_points', []))])}"""
        
        api_messages = [
            {'role': 'user', 'content': f'CONTEXT FOR THIS DEBATE:\n{context}\n\n---\nNow the user wants to discuss this. Here is their first message:'},
            {'role': 'assistant', 'content': "Understood. I have the full score report and the original argument in context. I'm ready to debate. What's your point?"}
        ] + messages
        
        response = call_groq(api_messages, DEBATE_SYSTEM, 600)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get all history"""
    try:
        history = get_all_history()
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<arg_id>', methods=['DELETE'])
def delete_history_item(arg_id):
    """Delete specific history item"""
    try:
        deleted = delete_argument(arg_id)
        if deleted:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Argument not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/save', methods=['POST'])
def save_to_history():
    """Manually save argument to history"""
    try:
        data = request.json
        arg_id = save_argument(data)
        return jsonify({'id': arg_id, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
