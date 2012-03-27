from flask import Flask,render_template
app = Flask(__name__)

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
app.debug = True
@app.route('/')
@app.route('/<name>')
def hello(name=None):
    return render_template('hello.jade', name=name)

if __name__ == "__main__":
    app.run()