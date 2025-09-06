import os
import json
import uuid
import duckdb
import traceback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from dotenv import load_dotenv
from vars import schema

# ============================================================
# 1. Setup
# ============================================================

load_dotenv()

# Initialise OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Path to DuckDB database
DB_PATH = "database/HDB_data.db"

# Output folder for visualisations
OUTPUT_DIR = "visualisation_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 2. Tool: Generate visualisations
# ============================================================

def generate_visualisation(sql_result: dict, python_code: str):
    """Execute LLM-generated Python visualisation code safely and save outputs."""
    try:
        result_id = str(uuid.uuid4())

        # Recreate DataFrame from SQL result
        df = pd.DataFrame(
            sql_result["result_df"]["rows"],
            columns=sql_result["result_df"]["columns"]
        )

        local_ns = {"pd": pd, "df": df, "px": px, "go": go}

        # Clean and run generated code
        python_code = python_code.replace("```python", "").replace("```", "").strip()
        exec(python_code, {}, local_ns)

        fig = local_ns.get("fig")
        if fig is None:
            return {"success": False, "error": "No `fig` variable created."}

        # Save PNG (requires kaleido)
        img_path = os.path.join(OUTPUT_DIR, f"{result_id}.png")
        img_bytes = fig.to_image(format="png")
        with open(img_path, "wb") as f:
            f.write(img_bytes)

        # Save JSON
        fig_json_path = os.path.join(OUTPUT_DIR, f"{result_id}_fig.json")
        with open(fig_json_path, "w") as f_json:
            f_json.write(fig.to_json())

        return {
            "success": True,
            "uuid": result_id,
            "code": python_code,
            "fig_path": fig_json_path,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "fig_path": None
        }

# ============================================================
# 3. Tool definitions for LLM
# ============================================================


tools = [
    {
    "type": "function",
    "function": {
      "name": "execute_sql_query",
      "description": "Execute the DuckDB SQL query and return the results.",
      "parameters": {
        "type": "object",
        "properties": {
          "sql_query": {
            "type": "string",
            "description": "The DuckDB SQL query to be executed."
          }
        },
        "required": ["sql_query"],
        "additionalProperties": False
      },
      "strict": True
    }
  },
    {
      "type": "function",
      "function": {
          "name": "execute_visualisation_code",
          "description": "Generate instructions for Python code to visualize the SQL query results.",
          "parameters": {
              "type": "object",
              "properties": {
                  ???: {
                      "type": "string",
                      "description": ???
                  }
              },
              "required": [???],
              "additionalProperties": False
          },
          "strict": True
      }
  },
]

# ============================================================
# 4. Tool implementations
# ============================================================

def execute_sql_query(sql_query: str):
    """Run SQL query against DuckDB."""
    if not sql_query:
        return {"error": "No SQL query provided"}
    try:
        conn = duckdb.connect(DB_PATH)
        c = conn.cursor()
        c.execute(sql_query)
        cols = [d[0] for d in c.description] if c.description else []
        rows = c.fetchmany(1000)
        conn.close()
        return {"result_df": {"columns": cols, "rows": rows}}
    except Exception as e:
        return {"error": f"Error executing SQL query: {str(e)}"}

def execute_visualisation_code(instructions: str, sql_result: dict):
    """Ask an LLM to generate Python visualisation code, then execute it."""
    prompt = f"""
    Given the following DuckDB SQL query result as a JSON-serializable dict:
    {json.dumps(sql_result, indent=2)}

    Write a self-contained Python snippet that: {???}

    Rules:
    - Data is already in a pandas DataFrame named `df`. Do NOT recreate it manually.
    - Use plotly.express or plotly.graph_objects -- we want interactive diagrams. Assign chart to variable `fig`.
    - Avoid fig.show().
    - Allowed libraries: pandas, plotly, matplotlib.
    - Style: transparent background, white font.
    - ONLY return the code.
    """
    messages = [{"role": "user", "content": prompt}]
    tries = 0

    while tries < 3:
        resp = client.chat.completions.create(
            model="qwen/qwen-2.5-coder-32b-instruct:free",
            messages=messages,
            temperature=???,
        )
        code = resp.choices[0].message.content.strip()
        print("\n📝 Generated visualisation code:\n", code)

        result = generate_visualisation(sql_result, code)
        if result["success"]:
            print("✅ Visualisation executed successfully.")
            return result
        else:
            print(f"⚠️ Visualisation failed: {result['error']}")
            messages.append({
                "role": "user",
                "content": f"Your code failed with error: {result['error']}. Fix it. Code was: {code}"
            })
            tries += 1

    return result

# ============================================================
# 5. Main agent loop
# ============================================================

def main_agent(user_input: str):
    messages = [
        {"role": "system", "content": f"""
        You are an agent that answers questions about HDB resale prices.

        This is the schema to the resale db named `resale_data_2017_to_2025`: {schema}

        Flow:
        1. If the user's query is just about the schema, answer directly.
        2. Otherwise, generate a SQL query and call `execute_sql_query`.
        3. {sentence abt calling viz tool}
        4. {sentence abt how if its just a single value answer, can skip viz}
        5. Give insights based on the data and (if created) the visualisation.

        Notes:
        - DO NOT redisplay tables or JSON filenames in markdown.
        - JUST give insights.
        - Remember to always include the tool name when calling a tool!

        Current year: 2025.
        """},
        {"role": "user", "content": user_input}
    ]

    results, viz_result = None, None

    while True:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=messages,
            tools=tools,
            temperature=0.2,
        )
        msg = response.choices[0].message
        messages.append(msg)

        # Debug: show raw message sometimes
        print("\n=== Raw LLM message ===")
        print(msg)

        if msg.tool_calls:
            for call in msg.tool_calls:
                name = call.function.name if call.function else None
                args = json.loads(call.function.arguments)

                if not name:
                    print("⚠️ Tool call missing name, ignoring.")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": "Tool call missing name."
                    })

                elif name == "execute_sql_query":
                    sql_query = args.get("sql_query")
                    print(f"\n🤖 Tool call: execute_sql_query\n📜 SQL: {sql_query}")
                    results = execute_sql_query(sql_query)
                    print(f"✅ SQL executed: {len(results['result_df']['rows'])} rows returned")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(results)
                    })

                elif name == "execute_visualisation_code":
                    instructions = ???
                    print(f"\n🤖 Tool call: execute_visualisation_code\n🖼️ Instructions: {instructions}")
                    viz_result = execute_visualisation_code(instructions, results)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(viz_result)
                    })

        else:
            # Final answer
            print("\n💡 Final insights:")
            print(msg.content)

            return {
                "insights": ???,
                "result_df": ??? if results else None,
                "visualisation": ??? if viz_result else None
            }

# ============================================================
# 6. Run example
# ============================================================

# if __name__ == "__main__":
#     output = main_agent("How has average resale price changed over the years?")

#     print("\n=== Insights ===")
#     print(output["insights"])

#     if output["result_df"]:
#         df = pd.DataFrame(output["result_df"]["rows"],
#                           columns=output["result_df"]["columns"])
#         print("\n=== Data Preview ===")
#         print(df.head())

#     if output.get("visualisation"):
#         print(f"\n=== Visualisation saved at: {output['visualisation']} ===")