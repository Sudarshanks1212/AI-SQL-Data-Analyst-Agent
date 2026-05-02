 # AI SQL DATA ANALYST AGENT (PRO VERSION)
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv("key.env")

# LangChain imports
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq

# PAGE CONFIG & STYLING
st.set_page_config(page_title="AI SQL Analyst", page_icon="🚀", layout="wide")

# Custom CSS for better padding and UI tweaks
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; padding-top: 10px; padding-bottom: 10px; }
    div[data-testid="stMetricValue"] { font-size: 28px; }
    </style>
""", unsafe_allow_html=True)

 
# HELPER FUNCTIONS
def clean_sql_query(raw_sql: str) -> str:
    """Removes markdown formatting from LLM SQL output securely."""
    cleaned = raw_sql.replace("```sql", "")
    cleaned = cleaned.replace("```SQL", "")
    cleaned = cleaned.replace("```", "")
    return cleaned.strip()

@st.cache_data
def convert_df_to_csv(dataframe):
    """Converts dataframe to CSV for downloading."""
    return dataframe.to_csv(index=False).encode('utf-8')

 
# SIDEBAR: CONFIGURATION & UPLOAD
with st.sidebar:
    st.header("⚙️ Setup & Configuration")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if groq_api_key:
        st.success("🔑 API Key securely loaded!")
    else:
        st.error("⚠️ GROQ_API_KEY not found in key.env!")
    
    st.divider()
    
    uploaded_file = st.file_uploader("📂 Upload CSV File", type=["csv"])
    
    if uploaded_file:
        st.success(f"Loaded: {uploaded_file.name}")
        
        # FEATURE 1: Data Schema Viewer in Sidebar
        df_preview = pd.read_csv(uploaded_file)
        st.divider()
        st.subheader("📋 Data Schema")
        st.write("Column Names & Data Types:")
        schema_df = pd.DataFrame(df_preview.dtypes, columns=['Data Type']).astype(str)
        st.dataframe(schema_df, use_container_width=True)


# MAIN APP LOGIC
st.title("🚀 AI SQL Data Analyst Agent")
st.markdown("Interact with your CSV data naturally. Ask questions, get insights, and generate charts!")

if not groq_api_key:
    st.info("👈 Please ensure your key.env file has your GROQ_API_KEY to begin.")
elif not uploaded_file:
    st.info("👈 Please upload a CSV file in the sidebar to begin.")
else:
    # 1. Load CSV & Init DB
    uploaded_file.seek(0) 
    df = pd.read_csv(uploaded_file)
    conn = sqlite3.connect("data.db")
    df.to_sql("data_table", conn, if_exists="replace", index=False)
    db = SQLDatabase.from_uri("sqlite:///data.db")

    # 2. Init LLM & Agent
    try:
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct", 
            temperature=0
        )
        agent = create_sql_agent(llm=llm, db=db, verbose=True)
    except Exception as e:
        st.error(f"Failed to initialize AI Agent: {e}")
        st.stop()

    # Dynamic Sample Questions
    sample_col = df.columns[0]
    num_cols = df.select_dtypes(include='number').columns.tolist()
    sample_num_col = num_cols[0] if num_cols else sample_col
    
    # 3. UI Layout (Tabs)
    tab_chat, tab_data, tab_about = st.tabs(["💬 Chat & Visualization", "🗄️ Raw Data & Statistics", "ℹ️ About the App"])

 
    # TAB: ABOUT THE APP
 
    with tab_about:
        st.markdown("### 🧠 About this AI Agent")
        st.write("Welcome to the **AI SQL Data Analyst**, a powerful tool designed to democratize data analysis. "
                 "This application allows you to upload any CSV file and ask questions about your data using plain, "
                 "natural language. No SQL or coding experience is required!")
        
        st.divider()
        
        col_hw, col_kf = st.columns(2)
        
        with col_hw:
            st.markdown("#### ⚙️ How it Works")
            st.write("1. **Data Ingestion:** Your CSV is securely loaded and converted into a temporary, lightning-fast SQLite database.")
            st.write("2. **AI Processing:** Using **LangChain** and the **Groq API** (Llama), your English questions are intelligently translated into complex SQL queries.")
            st.write("3. **Execution & Visualization:** The app runs the query, extracts the exact answer, and provides tools to chart the results instantly using **Plotly**.")
        
        with col_kf:
            st.markdown("#### ✨ Key Features")
            st.markdown("- **Natural Language to SQL:** Ask questions like *'What were the top 5 sales in Q3?'*")
            st.markdown("- **Smart Interactive Visualizations:** Auto-detects data types to prevent graph errors.")
            st.markdown("- **Automated Stats:** Instantly view data schemas and statistical summaries.")
            st.markdown("- **Exportable Insights:** Download your custom AI-generated query results as fresh CSV files.")
            
        st.divider()
        st.info("Built with ❤️ using Streamlit, Pandas, LangChain, Plotly, and Groq.")

  
    # TAB: RAW DATA & STATS
    
    with tab_data:
        st.subheader("📊 Dataset Preview")
        st.dataframe(df.head(15), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            st.metric("Total Columns", len(df.columns))
            
        # Statistical Summary
        if num_cols:
            st.divider()
            st.subheader("📈 Statistical Summary (Numerical Data)")
            st.dataframe(df.describe(), use_container_width=True)

 
    # TAB: CHAT & VISUALIZATION
     
    with tab_chat:
        
        with st.form("chat_form"):
            user_query = st.text_input(
                "💬 Ask a question about your data:", 
                placeholder=f"e.g., What is the total {sample_num_col} grouped by {sample_col}?"
            )
            submitted = st.form_submit_button("Send 🚀")

        if submitted and user_query:
            with st.spinner("🤖 Analyzing data and generating response..."):
                try:
                    # Run AI Agent for conversational response
                    response = agent.invoke({"input": user_query})
                    
                    st.success("Analysis Complete!")
                    st.markdown("### 🧠 AI Insight")
                    st.info(response["output"])

                    st.divider()

                    # Extract pure SQL using exact column names
                    actual_columns = ", ".join(df.columns.tolist())

                    prompt_sql = f"""
                    Convert this user question into a valid SQLite query.
                    Table name is 'data_table'.
                    The table has the following columns: {actual_columns}
                    
                    Question: {user_query}
                    
                    Rules:
                    - Return ONLY the raw SQL code. No markdown, no explanations.
                    - ONLY use the exact column names provided above. Do not invent column names.
                    """
                    raw_sql = llm.invoke(prompt_sql).content
                    sql_query = clean_sql_query(raw_sql)

                    # Execute SQL
                    result_df = pd.read_sql_query(sql_query, conn)

                    # Show outputs in columns
                    col_chart, col_table = st.columns([2, 1])

                    with col_table:
                        st.markdown("### 📋 Query Result")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Download Data Button
                        csv_data = convert_df_to_csv(result_df)
                        st.download_button(
                            label="📥 Download Result as CSV",
                            data=csv_data,
                            file_name='ai_query_result.csv',
                            mime='text/csv',
                            use_container_width=True
                        )
                        
                        with st.expander("🔍 Show Generated SQL"):
                            st.code(sql_query, language="sql")

                    with col_chart:
                        st.markdown("### 📊 Visualization")
                        if len(result_df.columns) >= 2 and len(result_df) > 0:
                            
                            # ✨ THE NEW SMART GRAPHING LOGIC ✨
                            all_cols = result_df.columns.tolist()
                            
                            # Find all columns that contain numbers
                            num_columns = result_df.select_dtypes(include=['number']).columns.tolist()
                            
                            c1, c2, c3 = st.columns(3)
                            
                            with c1: 
                                chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Line", "Scatter", "Area"])
                            
                            with c2: 
                                x_axis = st.selectbox("X-Axis (or Labels)", all_cols, index=0)
                            
                            with c3: 
                                if chart_type == "Pie":
                                    # Force the Pie chart to ONLY use numerical columns
                                    if not num_columns:
                                        st.error("Pie charts require numbers.")
                                        y_axis = None
                                    else:
                                        y_axis = st.selectbox("Y-Axis (Values)", num_columns, index=0)
                                else:
                                    # For other charts, try to default to a number if possible
                                    default_y = num_columns[0] if num_columns else (all_cols[1] if len(all_cols) > 1 else all_cols[0])
                                    default_index = all_cols.index(default_y) if default_y in all_cols else 0
                                    y_axis = st.selectbox("Y-Axis (or Values)", all_cols, index=default_index)

                            # Only try to draw the chart if we successfully picked a Y-Axis
                            if y_axis:
                                try:
                                    if chart_type == "Bar":
                                        fig = px.bar(result_df, x=x_axis, y=y_axis, template="plotly_white")
                                    elif chart_type == "Line":
                                        fig = px.line(result_df, x=x_axis, y=y_axis, template="plotly_white")
                                    elif chart_type == "Scatter":
                                        fig = px.scatter(result_df, x=x_axis, y=y_axis, template="plotly_white")
                                    elif chart_type == "Pie":
                                        # Check if there are negative numbers (which break pie charts)
                                        if (result_df[y_axis] < 0).any():
                                            st.warning("⚠️ Pie charts cannot display negative values. Please choose a different chart type.")
                                        else:
                                            fig = px.pie(result_df, names=x_axis, values=y_axis, template="plotly_white")
                                    elif chart_type == "Area":
                                        fig = px.area(result_df, x=x_axis, y=y_axis, template="plotly_white")
                                        
                                    if 'fig' in locals():
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                except Exception as chart_e:
                                    st.warning(f"Could not render {chart_type} chart. Try swapping your X and Y axes.")
                        else:
                            st.info("Not enough data points to generate a chart (requires at least 2 columns).")

                # FRIENDLY ERROR CATCHER
                except Exception as e:
                    error_msg = str(e).lower()
                    if "429" in error_msg or "rate limit" in error_msg:
                        st.warning("⏳ **Rate Limit Reached!** You have used up the free AI tokens for this model. Please wait about 10-15 minutes, or switch to a faster model.")
                    else:
                        st.error("❌ An error occurred during analysis. Please check your data or try rephrasing your question.")
                        with st.expander("Show detailed technical error"):
                            st.write(e)
