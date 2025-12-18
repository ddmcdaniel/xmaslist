import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration & Visuals
st.set_page_config(page_title="Christmas Wishlist", page_icon="🎄")
st.snow() # Festive snow effect

# Custom CSS for a Christmas Theme
st.markdown("""
    <style>
    .stApp { background-color: #fcfaf7; }
    div.stButton > button:first-child {
        background-color: #D42426; color: white; border-radius: 8px; border: none;
    }
    h1, h2, h3 { color: #165B33 !important; }
    [data-testid="stSidebar"] { background-color: #165B33; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def get_items():
    return conn.read(worksheet="items", ttl="0s")

def get_users():
    return conn.read(worksheet="users", ttl="0s")

# 3. Authentication Logic
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

if not st.session_state.authenticated:
    st.title("🎄 Christmas List Login")
    tab_login, tab_signup = st.tabs(["Login", "Create Account"])
    
    with tab_login:
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Login"):
            users_df = get_users()
            user_record = users_df[(users_df['username'] == u_in) & (users_df['password'] == str(p_in))]
            if not user_record.empty:
                st.session_state.authenticated = True
                st.session_state.user = u_in
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with tab_signup:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Sign Up"):
            users_df = get_users()
            if new_u in users_df['username'].values:
                st.warning("Username already exists!")
            else:
                new_row = pd.DataFrame([{"username": new_u, "password": new_p}])
                updated_users = pd.concat([users_df, new_row], ignore_index=True)
                conn.update(worksheet="users", data=updated_users)
                st.success("Account created! Now go to the Login tab.")

# 4. Main App (After Login)
else:
    current_user = st.session_state.user
    st.sidebar.title(f"🎁 Hello, {current_user}!")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    items_df = get_items()
    tab_mine, tab_others = st.tabs(["My Wishlist", "Claim for Others"])

    with tab_mine:
        st.subheader("Your Secret List")
        st.caption("Don't worry, you can't see who has claimed these!")
        my_items = items_df[items_df['owner'] == current_user]
        for i, row in my_items.iterrows():
            st.write(f"✅ {row['item']}")
        
        with st.form("add_item", clear_on_submit=True):
            new_item = st.text_input("Add something you want:")
            if st.form_submit_button("Add to List"):
                new_row = pd.DataFrame([{"id": len(items_df)+1, "owner": current_user, "item": new_item, "claimed_by": ""}])
                updated_items = pd.concat([items_df, new_row], ignore_index=True)
                conn.update(worksheet="items", data=updated_items)
                st.rerun()

    with tab_others:
        st.subheader("See what others want")
        others_items = items_df[items_df['owner'] != current_user]
        for i, row in others_items.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{row['owner']}** wants: {row['item']}")
            
            claimed_status = row['claimed_by']
            if pd.isna(claimed_status) or claimed_status == "":
                if c2.button("Claim", key=f"c_{i}"):
                    items_df.at[i, 'claimed_by'] = current_user
                    conn.update(worksheet="items", data=items_df)
                    st.rerun()
            elif claimed_status == current_user:
                c2.info("You claimed this!")
            else:
                c2.error("Taken")
