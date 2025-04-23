from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Tietokantamalli
class ReactionTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    reaction_time = db.Column(db.Float)

# luo tietokannan (vain ekalla kerralla)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

# REST API, palauttaa tiedot graafia varte
@app.route('/api/data')
def get_data():
    data = ReactionTime.query.order_by(ReactionTime.timestamp).all()
    return jsonify([
        {'timestamp': rt.timestamp.isoformat(), 'reaction_time': rt.reaction_time}
        for rt in data
    ])

# Raspi lähettää tänne POST
@app.route('/api/reaction', methods=['POST'])
def receive_data():
    data = request.json
    reaction_time = data.get('reaction_time')

    if reaction_time is not None:
        new_data = ReactionTime(reaction_time=reaction_time)
        db.session.add(new_data)
        db.session.commit()

        socketio.emit('new_reaction', {
            'timestamp': new_data.timestamp.isoformat(),
            'reaction_time': new_data.reaction_time
        })
        return {'status': 'OK'}
    return {'error': 'Missing data'}, 400

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
