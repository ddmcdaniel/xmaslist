import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Christmas Wishlist", page_icon="🎁")
st.snow()

# Christmas Styles
st.markdown("""
    <style>
    .stApp { background-color: #fcfaf7; }
    div.stButton > button:first-child {
        background-color: #D42426; color: white; border-radius: 8px;
    }
    h1, h2, h3 { color: #165B33 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Connection (Using the st-gsheets-connection library)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_items():
    # ttl="0" ensures we don't show old data if someone just added an item
    return conn.read(worksheet="items", ttl=0)

def get_users():
    return conn.read(worksheet="users", ttl=0)

# 3. Session State & Login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

if not st.session_state.authenticated:
    st.title("🎄 Christmas Registry Login")
    t1, t2 = st.tabs(["Login", "Create Account"])
    
    with t1:
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Log In"):
            users_df = get_users()
            # Convert password to string to match sheet data
            match = users_df[(users_df['username'] == u_in) & (users_df['password'].astype(str) == str(p_in))]
            if not match.empty:
                st.session_state.authenticated = True
                st.session_state.user = u_in
                st.rerun()
            else:
                st.error("Check your username/password.")

    with t2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Register"):
            users_df = get_users()
            if new_u in users_df['username'].values:
                st.error("User already exists!")
            else:
                new_user_df = pd.concat([users_df, pd.DataFrame([{"username": new_u, "password": new_p}])], ignore_index=True)
                conn.update(worksheet="users", data=new_user_df)
                st.success("Registered! Go to Login tab.")

# 4. Main App
else:
    st.sidebar.title(f"🎅 Hi, {st.session_state.user}!")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    items_df = get_items()
    tab_my, tab_buy = st.tabs(["My Wishlist", "Claim Gifts"])

    with tab_my:
        st.subheader("Your List")
        my_list = items_df[items_df['owner'] == st.session_state.user]
        for _, row in my_list.iterrows():
            st.write(f"🎁 {row['item']}")
        
        with st.form("add", clear_on_submit=True):
            item_name = st.text_input("What would you like?")
            if st.form_submit_button("Add Item"):
                new_data = pd.concat([items_df, pd.DataFrame([{
                    "id": len(items_df)+1, 
                    "owner": st.session_state.user, 
                    "item": item_name, 
                    "claimed_by": ""
                }])], ignore_index=True)
                conn.update(worksheet="items", data=new_data)
                st.rerun()

    with tab_buy:
        st.subheader("Gifts to Buy")
        others = items_df[items_df['owner'] != st.session_state.user]
        for i, row in others.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{row['owner']}** wants: {row['item']}")
            
            # Use index 'i' to find the correct row in the original items_df
            if pd.isna(row['claimed_by']) or row['claimed_by'] == "":
                if c2.button("Claim", key=f"btn_{i}"):
                    items_df.at[i, 'claimed_by'] = st.session_state.user
                    conn.update(worksheet="items", data=items_df)
                    st.rerun()
            elif row['claimed_by'] == st.session_state.user:
                c2.info("You got this!")
            else:
                c2.error("Claimed")
