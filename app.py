import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# ---------- Excel 讀取 ----------
df = pd.read_excel("agents.xlsx")

# ---------- 登入 ----------
st.sidebar.title("登入")
user_id = st.sidebar.text_input("請輸入身分證字號")
login_button = st.sidebar.button("登入")

if login_button:
    user_row = df[df["身分證字號"] == user_id]
    if user_row.empty:
        st.sidebar.error("身分證字號錯誤")
    else:
        st.session_state["user"] = user_row.iloc[0]
        st.success(f"歡迎 {user_row.iloc[0]['業務']}")

# ---------- 內勤篩選營業處 ----------
user_role = st.session_state.get("user", {}).get("角色", None)

if user_role in ["staff", "admin"]:
    selected_branch = st.selectbox("選擇營業處", options=df["營業處"].unique())
    df_filtered = df[df["營業處"] == selected_branch]
else:
    # agent 只看自己 + 下線
    user_id = st.session_state["user"]["身分證字號"]
    def get_downlines(uid):
        downlines = df[df["直屬身分證字號"] == uid]
        result = [uid]
        for dl in downlines["身分證字號"]:
            result += get_downlines(dl)
        return result
    ids = get_downlines(user_id)
    df_filtered = df[df["身分證字號"].isin(ids)]

# ---------- 顯示組織圖 ----------
G = nx.DiGraph()

for _, row in df_filtered.iterrows():
    G.add_node(row["身分證字號"], label=row["業務"])
for _, row in df_filtered.iterrows():
    if pd.notna(row["直屬身分證字號"]):
        G.add_edge(row["直屬身分證字號"], row["身分證字號"])

# fallback 排版，不依賴 pygraphviz
try:
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
except:
    pos = nx.spring_layout(G)

labels = nx.get_node_attributes(G, "label")
plt.figure(figsize=(12, 6))
nx.draw(G, pos, with_labels=True, labels=labels, node_size=2000, node_color="skyblue", arrows=True)
st.pyplot(plt)
