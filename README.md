# 🏠 Agentic AI Demo

Agentic AI walkthrough for **HDB resale analysis** → SQL → Data → Charts → Insights.

## ⚡ Tutorial Flow (4 steps)

1. **Calling an LLM API**

   * Setting up OpenRotuer API, ensuring dependencies are installed
   * 📄 File: `intro_to_tool_calling.py`

2. **Generate SQL query output by passing in DB Schema**

   * Instead of plaintext output, getting the LLM to give an SQL query
   * 📄 File: `intro_to_tool_calling.py`

3. **Tool Time! Creating a tool to execute the above generated SQL query & give insights **

   * Tool: `execute_sql_query`
   * 📄 File: `intro_to_tool_calling.py`

4. **Adding a Visualisation tool + Putting it all together!**

   * Add `execute_visualisation_code` tool & create plotly visualisations
   * Combine DB results + chart + analysis
   * 📄 Files:
       * `final.py` (Agent loop)
       * `app.py` (Streamlit UI)

5. **Dockerising & Deploying to Airbase**
   * Setting up Dockerfile
   * Linking repo to Airbase
   * Deploying to Airbase

## 🛠️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/<your-org>/agentic-ai-demo.git
cd agentic-ai-demo
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your OpenRouter API key

Create a `.env` file:

```bash
OPENROUTER_API_KEY=sk-your-key-here
```

---

## 🚀 Running the App

### Locally with Streamlit

```bash
streamlit run app.py
```

👉 Go to [http://localhost:8501](http://localhost:8501)

### With Docker

```bash
docker build -t agentic-ai-demo .
docker run -p 8501:8501 agentic-ai-demo
```

---