from kenversity import create_app
app = create_app("dev")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
