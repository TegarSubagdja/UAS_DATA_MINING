import streamlit as st

# Mendefinisikan elemen interaktif
user_input = st.text_input("Enter something:")
button_clicked = st.button("Click me")

# Callback untuk menanggapi interaksi tombol
if button_clicked:
    st.write(f"You clicked the button! Input: {user_input}")
