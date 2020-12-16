from websitem import app

if __name__ == '__main__':
    app.run(debug=True)

# User.query.all() --> returns all records
# User.query.first()
# USer.query.get(?) --> fetch user by id
# User.query.filter_by(username='?').all() --> query records acording to username
