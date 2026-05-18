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

# Primary and backup API keys
GROQ_API_KEYS = []

# Load primary key
primary_key = os.getenv('GROQ_API_KEY')
if primary_key:
    GROQ_API_KEYS.append(primary_key)

# Load backup key
backup_key = os.getenv('GROQ_API_KEY_2')
if backup_key:
    GROQ_API_KEYS.append(backup_key)

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

if not GROQ_API_KEYS:
    raise Exception('No GROQ_API_KEY found. Please set at least one API key.')

# System prompts - use regular strings (not f-strings) to avoid brace conflicts
SYSTEM_PROMPT = """You are a brutally precise argument analyst. Your job is to dissect the SPECIFIC argument provided and identify its EXACT flaws — not give generic writing advice.

Return ONLY a valid JSON object. No preamble, no code fences, no extra text whatsoever.

SCORING CRITERIA:
1. logic (integer 0-10): Are conclusions actually supported by the reasoning given IN THIS ARGUMENT?
2. evidence (integer 0-10): Does the argument cite concrete data, named studies, specific statistics, or real named examples?
3. clarity (integer 0-10): Is the argument's structure followable? Is the thesis identifiable?
4. depth (integer 0-10): Does the argument engage with complexity, counterarguments, or real-world nuance?
5. bias ("Low"/"Medium"/"High"): Does it acknowledge opposing views fairly?

MANDATORY SCORE RULES:
- No named studies, statistics, or concrete data → evidence MUST be ≤ 3
- Weak or absent causal reasoning → logic MUST be ≤ 4
- Only one perspective considered → bias CANNOT be "Low"
- Sweeping generalizations → bias = "High"
- Short or underdeveloped argument → depth MUST be ≤ 4

WEAKNESSES — each weakness MUST:
- Quote or closely paraphrase a specific phrase from the argument
- Name the exact logical problem by type
- Explain in 1-2 sentences why this specific flaw weakens THIS argument
- Minimum 2 weaknesses, maximum 6

IMPROVEMENT_POINTS — each point MUST:
- Target a specific claim or section of THIS argument
- Give a concrete, actionable thinking instruction
- Minimum 2 points, maximum 6

OUTPUT — return EXACTLY this JSON:
{
  "logic": <int 0-10>,
  "evidence": <int 0-10>,
  "clarity": <int 0-10>,
  "depth": <int 0-10>,
  "bias": "Low"|"Medium"|"High",
  "explanation": "<argument-specific 2-4 sentences>",
  "weaknesses": ["<specific weakness>", ...],
  "improvement_points": ["<specific actionable instruction>", ...],
  "confidence": "Low"|"Medium"|"High"
}"""

STRENGTHEN_SYSTEM = """You are an argument architect. You receive a weak or flawed argument and its scores. Your job is to rewrite it so it scores significantly higher under a strict evaluation rubric.

Return ONLY a valid JSON object with these fields:
{
  "improved_argument": "<the rewritten argument>",
  "changes_made": ["<list of specific changes made, 4-6 items>"]
}

THE SCORING RUBRIC YOU MUST SATISFY (the argument will be re-evaluated against these exact criteria):

LOGIC (target 7+):
- Every conclusion must follow explicitly from its premises
- Make causal chains visible: "If X then Y, because Z"
- No logical leaps, circular reasoning, or unstated assumptions
- PENALTY: Weak or absent causal reasoning forces logic score to 4 or below

EVIDENCE (target 6+):
- Cite at least one named real study, named statistic, or named institution with a concrete finding
- "Companies like Google" or "common patterns show" are NOT evidence and force evidence score to 3 or below
- Acceptable: "A 2015 Stanford study found...", "OECD 2022 data shows...", "Khan Academy internal data..."
- If no real study exists, use documented real-world cases with specificity: institution, year, measurable outcome
- PENALTY: No named studies or concrete data forces evidence score to 3 or below

CLARITY (target 7+):
- State the thesis clearly in the first 1-2 sentences
- Each paragraph has one clear function: thesis, evidence, counterargument, or conclusion
- No vague referents, ambiguous pronouns, or undefined terms

DEPTH (target 7+):
- Engage with at least one real counterargument and respond with reasoning, not dismissal
- Acknowledge the limits or conditions of your own claim explicitly
- PENALTY: Short or underdeveloped argument forces depth score to 4 or below

BIAS (target: Low):
- Acknowledge the strongest version of the opposing view before countering it
- Do not strawman or use loaded language against opposition
- PENALTY: Only one perspective considered means bias cannot be Low

HARD RULES:
- Preserve the original thesis — do not change what is being argued
- Write a complete standalone argument — no placeholders like [Study X] or [Source needed]
- Every sentence must add scoring value — no padding
- Length should be exactly as long as needed to satisfy the rubric, no longer"""

DEBATE_SYSTEM = """You are a rigorous debate partner and argument analyst. The user has submitted an argument which has been scored, and now they want to discuss it. You have the original argument and its full score report as context. 

Be intellectually honest: concede points that are valid, defend scores that are justified, ask clarifying questions when needed. Keep responses focused and sharp — 3-5 sentences unless a longer response is clearly warranted. No sycophancy."""

DIMENSION_EXPLAIN_SYSTEM = """You are an argument analyst. Given an argument and one of its scores on a specific dimension, explain in exactly 2-3 sentences WHY it received that SPECIFIC score. Start by stating: "You scored [X]/10 in [dimension] because..." Then reference actual phrases or claims from the argument to justify this exact score. Do not give generic advice."""

COMPARE_VERDICT_SYSTEM = """You are a debate judge. You have received two arguments and their scores. Write exactly 2 sentences: one declaring which argument is stronger and why, one identifying the single most decisive factor that separates them. Be blunt and specific."""


def call_groq(messages, system_prompt, max_tokens=2000):
    """Call Groq API with fallback to backup keys"""

    last_error = None

    for i, api_key in enumerate(GROQ_API_KEYS):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + api_key
            }

            payload = {
                'model': 'llama-3.3-70b-versatile',
                'temperature': 0.4,
                'max_tokens': max_tokens,
                'messages': [{'role': 'system', 'content': system_prompt}] + messages
            }

            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)

            if response.status_code == 429:
                last_error = 'Key ' + str(i+1) + ' rate limited'
                continue

            if not response.ok:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Groq API error ' + str(response.status_code))
                last_error = 'Key ' + str(i+1) + ': ' + error_msg
                continue

            data = response.json()
            return data['choices'][0]['message']['content'].strip()

        except requests.exceptions.Timeout:
            last_error = 'Key ' + str(i+1) + ': Request timeout'
            continue
        except Exception as e:
            last_error = 'Key ' + str(i+1) + ': ' + str(e)
            continue

    raise Exception('All API keys failed. Last error: ' + last_error)


def parse_json(text):
    """Parse JSON from LLM response"""
    clean = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    clean = re.sub(r'\s*```$', '', clean)
    clean = clean.strip()

    match = re.search(r'\{[\s\S]*\}', clean)
    if match:
        clean = match.group(0)

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise Exception('Invalid JSON from model: ' + e.msg)


def normalize_score_result(parsed, argument_text):
    """Normalize and calculate scores"""
    logic = max(0, min(10, int(parsed.get('logic', 0))))
    evidence = max(0, min(10, int(parsed.get('evidence', 0))))
    clarity = max(0, min(10, int(parsed.get('clarity', 0))))
    depth = max(0, min(10, int(parsed.get('depth', 0))))

    bias_str = parsed.get('bias', 'Medium')
    if bias_str not in ['Low', 'Medium', 'High']:
        bias_str = 'Medium'

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

        prompt = 'ARGUMENT TO EVALUATE:\n\n' + argument + '\n\nAnalyze ONLY this specific argument. Quote or reference actual phrases from it. Return ONLY the JSON object.'
        

        raw_response = call_groq(
            [{'role': 'user', 'content': prompt}],
            SYSTEM_PROMPT,
            2000
        )

        parsed = parse_json(raw_response)
        result = normalize_score_result(parsed, argument)

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

        score_context = ''
        if scores:
            score_context = 'CURRENT SCORES:
Logic: ' + str(scores.get('logic', 0)) + '/10, Evidence: ' + str(scores.get('evidence', 0)) + '/10, Clarity: ' + str(scores.get('clarity', 0)) + '/10, Depth: ' + str(scores.get('depth', 0)) + '/10

Weaknesses identified:
' + '
'.join(scores.get('weaknesses', []))
        else:
            score_context = 'No prior scores available — analyze and improve the argument holistically.'

        prompt = 'ORIGINAL ARGUMENT:
' + argument + '

' + score_context + '

Rewrite this argument to be significantly stronger. Return only the JSON object.'

        raw_response = call_groq(
            [{'role': 'user', 'content': prompt}],
            STRENGTHEN_SYSTEM,
            1200
        )

        parsed = parse_json(raw_response)

        improved_arg = parsed.get('improved_argument', '')
        if improved_arg:
            rescore_prompt = 'ARGUMENT TO EVALUATE:

' + improved_arg.strip() + '

Analyze ONLY this specific argument. Return ONLY the JSON object.'
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

        prompt_a = 'ARGUMENT TO EVALUATE:

' + arg_a + '

Return ONLY the JSON object.'
        raw_a = call_groq([{'role': 'user', 'content': prompt_a}], SYSTEM_PROMPT, 1500)
        parsed_a = parse_json(raw_a)
        result_a = normalize_score_result(parsed_a, arg_a)

        prompt_b = 'ARGUMENT TO EVALUATE:

' + arg_b + '

Return ONLY the JSON object.'
        raw_b = call_groq([{'role': 'user', 'content': prompt_b}], SYSTEM_PROMPT, 1500)
        parsed_b = parse_json(raw_b)
        result_b = normalize_score_result(parsed_b, arg_b)

        verdict_prompt = 'ARGUMENT A (Score: ' + str(result_a['overall_score']) + '/10):
' + result_a['argument'] + '

ARGUMENT B (Score: ' + str(result_b['overall_score']) + '/10):
' + result_b['argument'] + '

Write a 2-sentence verdict: which is stronger and why, and the single most decisive factor.'

        verdict = call_groq(
            [{'role': 'user', 'content': verdict_prompt}],
            COMPARE_VERDICT_SYSTEM,
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

        weaknesses_text = '
'.join([str(i+1) + '. ' + w for i, w in enumerate(scores.get('weaknesses', []))])
        improvements_text = '
'.join([str(i+1) + '. ' + p for i, p in enumerate(scores.get('improvement_points', []))])

        context = 'ORIGINAL ARGUMENT:
' + argument + '

SCORE REPORT:
Logic: ' + str(scores.get('logic', 0)) + '/10
Evidence: ' + str(scores.get('evidence', 0)) + '/10
Clarity: ' + str(scores.get('clarity', 0)) + '/10
Depth: ' + str(scores.get('depth', 0)) + '/10
Bias: ' + scores.get('bias', 'Medium') + '
Overall: ' + str(scores.get('overall_score', 0)) + '/10

Explanation: ' + scores.get('explanation', '') + '

Weaknesses:
' + weaknesses_text + '

Improvement Points:
' + improvements_text

        api_messages = [
            {'role': 'user', 'content': 'CONTEXT FOR THIS DEBATE:
' + context + '

---
Now the user wants to discuss this. Here is their first message:'},
            {'role': 'assistant', 'content': "Understood. I have the full score report and the original argument in context. I'm ready to debate. What's your point?"}
        ] + messages

        response = call_groq(api_messages, DEBATE_SYSTEM, 600)

        return jsonify({'response': response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/explain', methods=['POST'])
def explain_dimension():
    """Explain a specific dimension score"""
    try:
        data = request.json
        argument = data.get('argument', '')
        dimension = data.get('dimension', '')
        value = data.get('value', 0)

        if not argument or not dimension:
            return jsonify({'error': 'Argument and dimension required'}), 400

        prompt = 'Argument:
' + argument + '

This argument scored ' + str(value) + '/10 on ' + dimension + '. Explain why in 2-3 sentences, referencing specific phrases.'
        response = call_groq(
            [{'role': 'user', 'content': prompt}],
            DIMENSION_EXPLAIN_SYSTEM,
            300
        )

        return jsonify({'explanation': response})

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
