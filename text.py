import streamlit as st

if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False

def callback():
    st.session_state.button_clicked = True

if st.button("Open next part", on_click=callback) or st.session_state.button_clicked:
    if st.button("pop out balloons"):
        st.balloons()
