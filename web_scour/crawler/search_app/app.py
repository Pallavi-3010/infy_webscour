from flask import Flask, render_template, request
import json
import string

app = Flask(__name__)

# ---------------- LOAD INDEX DATA ----------------
with open("../indexer/inverted_index.json", "r", encoding="utf-8") as f:
    inverted_index = json.load(f)

with open("../indexer/idf.json", "r", encoding="utf-8") as f:
    idf = json.load(f)

# ---------------- TOKENIZER ----------------
def tokenize(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.split()

# ---------------- SEARCH WITH SCORING ----------------
def search(query, top_k=5):
    scores = {}
    tokens = tokenize(query)

    for word in tokens:
        if word not in inverted_index:
            continue

        for item in inverted_index[word]:
            doc_id = item[0]
            tf = item[1]

            score = tf * idf.get(word, 0)
            scores[doc_id] = scores.get(doc_id, 0) + score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

# ---------------- ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "")
        results = search(query)

    return render_template("index.html", query=query, results=results)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
