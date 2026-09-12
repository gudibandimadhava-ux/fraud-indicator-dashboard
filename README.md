# Fraud Indicator Dashboard

A Streamlit dashboard analyzing insurance fraud indicators, built for
Internal Assignment 2 (Option C — Fraud Indicator Dashboard).

## What's in this folder
- `app.py` — the dashboard itself
- `data_prep.py` — cleans and joins the raw data (run this first)
- `data/` — raw CSVs (claims, fraud_indicators, policies) + the cleaned
  files data_prep.py produces
- `requirements.txt` — Python packages needed

## Run it locally
```
pip install -r requirements.txt
python data_prep.py      # only needed once, or after changing raw data
streamlit run app.py
```
Then open the local URL it prints (usually http://localhost:8501).

## Deploy it online (see step-by-step guide in chat)
1. Push this whole folder to a new GitHub repository.
2. Go to https://share.streamlit.io, sign in with GitHub.
3. Point it at your repo, branch `main`, main file `app.py`.
4. Click Deploy — you'll get a public URL to put in your walkthrough doc.
