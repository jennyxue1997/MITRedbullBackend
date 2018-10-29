from flask import Flask, request, jsonify
from flask_cors import CORS
import champ_select
import time_to_win
app = Flask(__name__)
CORS(app)

@app.route('/', methods=["POST"])
def get_optimal_champs():
    return jsonify(champ_select.get_best_champ_select(request))

@app.route('/time', methods=["GET", "POST"])
def get_optimal_win_time():
    return jsonify(time_to_win.get_best_time_to_win(request))

if __name__ == "__main__":
    app.run()
