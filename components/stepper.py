import streamlit as st

def render_stepper(current_step: int):
    """
    Renders 1 — 2 — 3 — 4 circular progress stepper with zero outer boxes, borders, or cards.
    """
    steps = [1, 2, 3, 4]
    items_html = ""
    for i, step in enumerate(steps):
        if step == current_step:
            circle_style = "width: 34px; height: 34px; border-radius: 50%; background-color: #2563EB; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; font-family: sans-serif; box-shadow: 0 0 0 3px rgba(37,99,235,0.25);"
        elif step < current_step:
            circle_style = "width: 34px; height: 34px; border-radius: 50%; background-color: #0B192C; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; font-family: sans-serif;"
        else:
            circle_style = "width: 34px; height: 34px; border-radius: 50%; background-color: #E2E8F0; color: #64748B; display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; font-family: sans-serif; border: 1px solid #CBD5E1;"
            
        items_html += f'<div style="{circle_style}">{step}</div>'
        
        if i < len(steps) - 1:
            line_color = "#0B192C" if step < current_step else "#CBD5E1"
            items_html += f'<div style="width: 50px; height: 2px; background-color: {line_color}; margin: 0 10px;"></div>'

    html = f"""
    <div style="display: flex; align-items: center; justify-content: center; margin: 4px 0 18px 0; padding: 0; background: transparent; border: none; box-shadow: none;">
        {items_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
