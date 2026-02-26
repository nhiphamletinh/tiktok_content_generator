from flask import Flask, render_template, jsonify, request
import subprocess
import sys
import os
import json

app = Flask(__name__, static_folder="static", template_folder="templates")

PY = sys.executable

def run_script(name):
    """Run a python script in the current repo using the environment's python."""
    path = os.path.join(os.getcwd(), name)
    if not os.path.exists(path):
        return False, f"Script not found: {path}"
    try:
        proc = subprocess.run([PY, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        out = proc.stdout.decode("utf-8", errors="ignore")
        return proc.returncode == 0, out
    except Exception as e:
        return False, str(e)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    # 1) embeddings (local)
    ok, out = run_script('embedding_pipeline_local.py')
    if not ok:
        return jsonify({'ok': False, 'step': 'embed', 'error': out}), 500

    # 2) clustering
    ok, out = run_script('cluster_insights.py')
    if not ok:
        return jsonify({'ok': False, 'step': 'cluster', 'error': out}), 500

    # load clusters.json
    try:
        with open('clusters.json', 'r', encoding='utf-8') as f:
            clusters = json.load(f)
    except Exception as e:
        return jsonify({'ok': False, 'step': 'read_clusters', 'error': str(e)}), 500

    # send clusters to frontend
    return jsonify({'ok': True, 'clusters': clusters})


@app.route('/recommend', methods=['POST'])
def recommend():
    # run comment_insights to generate cluster_insights.json
    ok, out = run_script('comment_insights.py')
    if not ok:
        return jsonify({'ok': False, 'step': 'insights', 'error': out}), 500

    try:
        with open('cluster_insights.json', 'r', encoding='utf-8') as f:
            insights = json.load(f)
    except Exception as e:
        return jsonify({'ok': False, 'step': 'read_insights', 'error': str(e)}), 500

    return jsonify({'ok': True, 'insights': insights})


if __name__ == '__main__':
    # Run dev server. In production use a proper WSGI server.
    app.run(host='0.0.0.0', port=8501, debug=True)
