from flask import Flask, request
from flask_cors import CORS, cross_origin
from audio_service import AudioService

app = Flask(__name__)
cors = CORS(app)
audioService = AudioService()


@app.route(r'/api/problem-data', methods=['POST'])
@cross_origin()
def createProblemData():
    payload = request.get_json()
    sounds = payload['sounds']
    try:
        segments = audioService.gen_problem_data(sounds)
        return segments
    except:
        return "Could not create problem data!"


@app.route(r'/api/divided-data', methods=['POST'])
@cross_origin()
def createDividedData():
    payload = request.get_json()
    problemData = payload['problemData']
    durations = payload['durations']
    try:
        segments = audioService.gen_divided_data(problemData, durations)
        return segments
    except:
        return "Could not create divided data!"


if __name__ == '__main__':
    app.run(host="localhost", port=5555)
