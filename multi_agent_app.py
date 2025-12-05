# multi_agent_app.py
"""
Multi-Agent Data Analysis System
Streamlit application for orchestrating AI agents for data analysis.
"""

import streamlit as st
import time
from snowflake.snowpark.context import get_active_session

# Import agents from the agents package
from agents import AgentOrchestrator

# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.set_page_config(
        page_title="Multi-Agent Data Analysis System",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Multi-Agent Data Analysis System")
    st.markdown("*MVP Version - Powered by Snowflake Cortex*")
    
    # Get Snowflake Session (for Streamlit in Snowflake)
    try:
        session = get_active_session()
    except:
        st.error("Failed to get Snowflake session. Make sure you're running in Streamlit in Snowflake.")
        st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Agent Configuration")
        
        st.subheader("1️⃣ Data Collection Agent")
        collector_prompt = st.text_area(
            "Data Query Requirement",
            "SELECT * FROM CUSTOMERS LIMIT 1000",
            height=100,
            help="Describe what data you need, Agent will generate SQL"
        )
        
        # Optional: Provide available table list
        with st.expander("Advanced: Specify Available Tables"):
            available_tables = st.text_input(
                "Available tables (comma-separated)",
                "CUSTOMERS,ORDERS,TRANSACTIONS"
            )
        
        st.divider()
        
        st.subheader("2️⃣ Data QA Agent")
        qa_prompt = st.text_area(
            "Special Check Requirements (leave empty for standard)",
            "",
            height=80,
            help="Leave empty to execute standard QC process"
        )
        
        st.divider()
        
        st.subheader("3️⃣ Business Analyst Agent")
        analyst_prompt = st.text_area(
            "Analysis Focus",
            "Identify main causes of customer churn",
            height=80
        )
        
        st.divider()
        
        st.info("4️⃣ Compliance Agent will automatically check for PII")
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        run_button = st.button("🚀 Start Analysis", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.rerun()
    
    # Execute analysis
    if run_button:
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(value, text):
            progress_bar.progress(value)
            status_text.text(text)
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(session)
        
        # Prepare prompts
        user_prompts = {
            "collector": collector_prompt,
            "qa": qa_prompt,
            "analyst": analyst_prompt
        }
        
        if available_tables:
            user_prompts["available_tables"] = [t.strip() for t in available_tables.split(',')]
        
        # Execute pipeline
        with st.spinner("Agents working..."):
            results = orchestrator.run_pipeline(user_prompts, update_progress)
        
        progress_bar.empty()
        status_text.empty()
        
        # Check for errors
        if "error" in results:
            st.error(f"❌ {results['error']}")
            st.json(results.get("details", {}))
            st.stop()
        
        # Display results
        st.success("✅ Analysis completed!")
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Data Collection", 
            "✅ Quality Check", 
            "💡 Business Insights", 
            "🔒 Compliance Check",
            "📋 Execution Log"
        ])
        
        # Tab 1: Data Collection
        with tab1:
            st.subheader("Collected Data")
            collector_result = results.get('data_collector_result', {})
            
            if collector_result.get('status') == 'success':
                st.code(collector_result['query'], language='sql')
                st.metric("Row Count", collector_result['row_count'])
                st.metric("Column Count", len(collector_result['columns']))
                
                st.dataframe(
                    collector_result['data'],
                    use_container_width=True,
                    height=400
                )
                
                # Download button
                csv = collector_result['data'].to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "data.csv",
                    "text/csv"
                )
            else:
                st.error(collector_result.get('error', 'Unknown error'))
        
        # Tab 2: Quality Check
        with tab2:
            st.subheader("Data Quality Analysis")
            qa_result = results.get('data_qa_result', {})
            
            if qa_result.get('status') == 'success':
                # Display summary
                st.markdown("### 📝 Summary")
                st.info(qa_result['summary'])
                
                # Display issues
                if qa_result['issues_found'] > 0:
                    st.warning(f"⚠️ Found {qa_result['issues_found']} data quality issues")
                    for issue in qa_result['analysis']['issues']:
                        st.write(f"- {issue}")
                else:
                    st.success("✅ No data quality issues found")
                
                # Display detailed analysis
                with st.expander("Detailed Analysis Results"):
                    st.json(qa_result['analysis'])
            else:
                st.error(qa_result.get('error', 'Unknown error'))
        
        # Tab 3: Business Insights
        with tab3:
            st.subheader("Business Analysis")
            business_result = results.get('business_result', {})
            
            if business_result.get('status') == 'success':
                st.markdown(business_result['insights'])
                
                # Highlight recommendations
                if business_result.get('recommendations'):
                    st.markdown("### 🎯 Key Recommendations")
                    for i, rec in enumerate(business_result['recommendations'], 1):
                        st.info(f"**{i}.** {rec}")
            else:
                st.error(business_result.get('error', 'Unknown error'))
        
        # Tab 4: Compliance Check
        with tab4:
            st.subheader("Compliance Check Results")
            compliance_result = results.get('compliance_result', {})
            
            if compliance_result.get('approved'):
                st.success("✅ Compliance check passed - No privacy issues found")
            else:
                st.error("❌ Compliance check failed")
                
                if compliance_result.get('pii_detected'):
                    st.warning("The following issues were detected:")
                    for issue in compliance_result['pii_detected']:
                        st.write(f"- {issue}")
            
            with st.expander("LLM Semantic Check Results"):
                st.write(compliance_result.get('llm_check', 'None'))
        
        # Tab 5: Execution Log
        with tab5:
            st.subheader("Execution Log")
            for log in orchestrator.execution_log:
                st.text(f"⏱️ {time.strftime('%H:%M:%S', time.localtime(log['timestamp']))} - {log['message']}")

# ============================================
# RUN APPLICATION
# ============================================
# Call main() directly for Snowflake Streamlit
main()