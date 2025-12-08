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
        st.header("⚙️ System Configuration")

        # LLM Selection
        st.subheader("🤖 LLM Model Selection")
        llm_model = st.selectbox(
            "Select LLM Model",
            options=[
                "snowflake-arctic",
                "mistral-large2",
                "llama3.1-70b",
                "llama3.1-405b",
                "reka-flash",
                "mixtral-8x7b",
                "gemma-7b"
            ],
            index=0,
            help="Choose which LLM model to use for all agents"
        )

        st.divider()
        st.header("⚙️ Agent Configuration")

        st.subheader("1️⃣ Data Collection Agent")
        collector_prompt = st.text_area(
            "Data Query Requirement (Optional - Use Question field below instead)",
            "",
            height=100,
            help="This field is optional. Your main question should be entered in the '❓ Your Question' field below. This is only for advanced SQL query customization."
        )

        # Metadata/Context for better SQL generation
        # Use auto-discovered schema if available
        default_schema = st.session_state.get('auto_schema_context', '')
        metadata_context = st.text_area(
            "📋 Database Schema Context (Optional)",
            value=default_schema,
            placeholder="Example:\n- USAGE_DATA table contains: user_id, timestamp, action, device_type\n- CUSTOMERS table contains: customer_id, name, signup_date, plan_type\n- Tables are related by user_id = customer_id",
            height=120,
            help="Provide information about your tables, columns, and relationships to help generate better SQL queries. Click 'Discover Available Tables' below to auto-populate this field."
        )

        # Optional: Provide available table list
        with st.expander("Advanced: Specify Available Tables"):
            available_tables = st.text_input(
                "Available tables (comma-separated)",
                "Leave empty to auto-discover tables"
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
            "Analyze usage patterns and identify key trends",
            height=80
        )
        
        st.divider()
        
        st.info("4️⃣ Compliance Agent will automatically check for PII")

    # Main interface
    st.header("❓ Your Question")

    # Add a button to discover available tables
    if st.button("🔍 Discover Available Tables & Auto-Fill Schema", help="Click to discover tables and automatically populate schema context"):
        try:
            # Query to get all tables in current schema
            tables_query = "SHOW TABLES"
            tables_df = session.sql(tables_query).to_pandas()

            if not tables_df.empty:
                st.success(f"Found {len(tables_df)} tables in your database:")
                # Display table names
                table_names = tables_df['name'].tolist() if 'name' in tables_df.columns else tables_df.iloc[:, 1].tolist()

                # Show in columns for better display
                cols = st.columns(3)
                for idx, table_name in enumerate(table_names):
                    cols[idx % 3].write(f"• `{table_name}`")

                # Build schema context automatically
                schema_context_lines = []
                st.info("🔍 Discovering column information for each table...")

                for table_name in table_names[:10]:  # Limit to first 10 tables to avoid timeouts
                    try:
                        # Get column info for each table
                        desc_query = f"DESCRIBE TABLE {table_name}"
                        desc_df = session.sql(desc_query).to_pandas()

                        if not desc_df.empty:
                            # Extract column names
                            col_names = desc_df['name'].tolist() if 'name' in desc_df.columns else desc_df.iloc[:, 0].tolist()
                            # Limit to first 10 columns to keep it concise
                            col_names_str = ', '.join(col_names[:10])
                            if len(col_names) > 10:
                                col_names_str += f", ... ({len(col_names)} total columns)"

                            schema_context_lines.append(f"- {table_name} table contains: {col_names_str}")
                    except Exception as e:
                        schema_context_lines.append(f"- {table_name} table (could not fetch columns)")

                # Store in session state to auto-populate the text area
                auto_schema_context = "\n".join(schema_context_lines)
                st.session_state['auto_schema_context'] = auto_schema_context

                st.success("✅ Schema context has been auto-populated in the sidebar! Scroll down and check the 'Database Schema Context' field.")

                with st.expander("📋 Preview of Auto-Generated Schema Context"):
                    st.code(auto_schema_context, language="text")
            else:
                st.warning("No tables found in the current schema.")
        except Exception as e:
            st.error(f"Error discovering tables: {str(e)}")

    user_question = st.text_area(
        "Enter your data analysis question",
        placeholder="Example: What are the top 5 users by usage? How many active users do we have this month?",
        height=100,
        help="Enter your question here. The agents will work together to answer it by collecting data, checking quality, and providing insights."
    )

    # Show reminder if no schema context is provided
    if not st.session_state.get('auto_schema_context', ''):
        st.info("💡 **Tip:** Click the '🔍 Discover Available Tables & Auto-Fill Schema' button above to automatically detect your database schema for better results!")

    st.divider()

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
        
        # Initialize orchestrator with selected LLM model
        orchestrator = AgentOrchestrator(session, llm_model=llm_model)

        # Prepare prompts
        user_prompts = {
            "collector": collector_prompt,
            "qa": qa_prompt,
            "analyst": analyst_prompt,
            "metadata_context": metadata_context if metadata_context else "",
            "user_question": user_question if user_question else ""
        }

        if available_tables and available_tables != "Leave empty to auto-discover tables":
            user_prompts["available_tables"] = [t.strip() for t in available_tables.split(',')]
        
        # Execute pipeline
        with st.spinner("Agents working..."):
            results = orchestrator.run_pipeline(user_prompts, update_progress)
        
        progress_bar.empty()
        status_text.empty()
        
        # Check for errors
        if "error" in results:
            st.error(f"❌ {results['error']}")

            # Show details if available
            details = results.get("details", {})
            if details:
                with st.expander("📋 Error Details"):
                    st.json(details)

                # If there's an error message with table suggestions, highlight it
                error_msg = details.get('error', '')
                if 'Available tables' in error_msg:
                    st.warning("⚠️ It looks like the query used a table that doesn't exist. Please click '🔍 Discover Available Tables & Auto-Fill Schema' and try again.")

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