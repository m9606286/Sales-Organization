import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="晨暉業務系統", layout="wide")

st.title("📊 晨暉業務組織系統")
st.caption("用身分證號登入｜內勤可依營業處篩選｜agent只看自己與下線")

# ===== 讀取 Excel =====
@st.cache_data
def load_data():
    return pd.read_excel("agents.xlsx")

df = load_data()

# ===== Session =====
if "login" not in st.session_state:
    st.session_state.login = False

# ===== 登入畫面 =====
if not st.session_state.login:
    st.subheader("🔐 系統登入")
    id_input = st.text_input("請輸入身分證號", placeholder="A123456789").strip().upper()

    if st.button("登入"):
        # 用身分證號登入
        user = df[df["身分證字號"] == id_input]

        if user.empty:
            st.error("查無此身分證號")
        else:
            st.session_state.login = True
            st.session_state.user = user.iloc[0].to_dict()
            st.experimental_rerun()

    st.stop()

# ===== 已登入 =====
user = st.session_state.user
st.sidebar.success(f"登入成功：{user['業務']}")
st.sidebar.write(f"角色：{user.get('角色','agent')}")

if st.sidebar.button("登出"):
    st.session_state.clear()
    st.experimental_rerun()

# ===== 內勤 / 管理員可篩選營業處 =====
role = user.get("角色","agent")
if role in ["admin","staff"]:
    sales_dept_options = df["營業處"].unique().tolist()
    selected_dept = st.sidebar.multiselect("選擇營業處篩選", sales_dept_options, default=sales_dept_options)
    df_filtered = df[df["營業處"].isin(selected_dept)]
else:
    df_filtered = df.copy()  # agent 就看全部資料，但後面組織圖會限制

# ===== 建立組織圖 =====
G = nx.DiGraph()

for _, row in df_filtered.iterrows():
    # 節點用身分證號，顯示姓名（業務）
    G.add_node(row["身分證字號"], label=row["業務"])

for _, row in df_filtered.iterrows():
    # 直屬身分證字號作為上級
    if pd.notna(row["直屬身分證字號"]):
        G.add_edge(row["直屬身分證字號"], row["身分證字號"])

# ===== 權限判斷 =====
if role in ["admin","staff"]:
    visible_nodes = list(G.nodes)
else:
    # agent 只看自己與下線
    visible_nodes = nx.descendants(G, user["身分證字號"]) | {user["身分證字號"]}

subG = G.subgraph(visible_nodes)

# ===== 顯示組織圖 =====
st.subheader("🌳 業務組織圖")

plt.figure(figsize=(14,10))
try:
    pos = nx.nx_agraph.graphviz_layout(subG, prog="dot")
except:
    pos = nx.spring_layout(subG)

labels = {n: G.nodes[n]['label'] for n in subG.nodes}

nx.draw(
    subG,
    pos,
    labels=labels,
    node_size=2600,
    node_color=[
        "#FFD966" if n == user["身分證字號"] else "#A7C7E7"
        for n in subG.nodes
    ],
    font_size=10,
    font_weight="bold",
    arrows=True
)

st.pyplot(plt)

# ===== 管理員 / 內勤表格 =====
if role in ["admin","staff"]:
    st.subheader("📋 業務資料表")
    st.dataframe(df_filtered)
