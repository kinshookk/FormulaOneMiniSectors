import streamlit as st
import model as m


st.set_page_config(page_title="F1 Qualifying Analysis", layout="wide")
    
st.title("Formula 1 Qualifying Analysis")
st.write("Compare the pole position lap with P2 for any Formula 1 qualifying session")
    
# Year selection
available_years = list(range(2018, 2025)) 
year = st.selectbox("Select Year", available_years, index=len(available_years)-2)
    
# Get available events for selected year
events = m.get_available_events(year)
event = st.selectbox("Select Grand Prix", events)
    
if st.button("Generate Analysis"):
    try:
        with st.spinner("Loading session data..."):
            session = m.fastf1.get_session(year, event, 'Q')
            session.load()
            
        with st.spinner("Creating visualization..."):
            fig = m.create_minisector_plot(session)
            st.pyplot(fig)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("This could be due to missing data for the selected session or other issues. Please try another race.")
