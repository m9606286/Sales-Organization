import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

# 1. 頁面設定
st.set_page_config(page_title="晨暉業務組織架構圖", layout="wide")

# 2. 讀取與處理資料 (從你提供的檔案格式)
@st.cache_data
def load_and_clean_data(file_path):
    df = pd.read_csv(file_path)
    # 確保空值處理，避免遞迴出錯
    df['parent'] = df['parent'].fillna("")
    df['role'] = df['role'].fillna("職員")
    return df

def build_tree(df, parent_name):
    """遞迴建立樹狀結構"""
    children_df = df[df['parent'] == parent_name]
    nodes = []
    for _, row in children_df.iterrows():
        nodes.append({
            "name": f"{row['name']}\n{row['role']}",
            "children": build_tree(df, row['name'])
        })
    return nodes

# 3. 介面設計
st.title("📂 晨暉業務組織管理系統")
st.markdown("---")

# 側邊欄設定
st.sidebar.header("圖表設定")
direction = st.sidebar.selectbox("佈局方向", ["從左至右 (LR)", "從上至下 (TB)"])
orient = "LR" if direction == "從左至右 (LR)" else "TB"

# 載入資料 (請確保檔案路徑正確，或改用 st.file_uploader)
try:
    # 這裡直接讀取你上傳的檔案
    df = load_and_clean_data("晨暉業務組織.xlsx - 工作表1.csv")
    
    # 尋找根節點 (沒有主管的人)
    roots = df[df['parent'] == ""]
    if roots.empty:
        st.error("找不到根節點，請確認資料中是否有人的主管欄位為空。")
    else:
        # 建立樹狀 JSON
        root_name = roots.iloc[0]['name']
        root_role = roots.iloc[0]['role']
        tree_data = {
            "name": f"{root_name}\n{root_role}",
            "children": build_tree(df, root_name)
        }

        # 4. ECharts 參數設定
        options = {
            "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
            "series": [
                {
                    "type": "tree",
                    "data": [tree_data],
                    "top": "5%",
                    "left": "15%",
                    "bottom": "5%",
                    "right": "15%",
                    "symbolSize": 10,
                    "orient": orient,  # 水平或垂直
                    "label": {
                        "position": "top" if orient == "TB" else "left",
                        "verticalAlign": "middle",
                        "align": "right" if orient == "LR" else "center",
                        "fontSize": 12,
                        "fontWeight": "bold"
                    },
                    "leaves": {
                        "label": {
                            "position": "bottom" if orient == "TB" else "right",
                            "verticalAlign": "middle",
                            "align": "center" if orient == "TB" else "left"
                        }
                    },
                    "emphasis": {"focus": "descendant"},
                    "expandAndCollapse": True, # 點擊節點可收合
                    "initialTreeDepth": 2,      # 預設展開層級
                    "animationDurationUpdate": 750,
                }
            ],
        }

        # 搜尋功能
        search_query = st.sidebar.text_input("🔍 搜尋姓名或職稱")
        if search_query:
            match = df[df['name'].str.contains(search_query) | df['role'].str.contains(search_query)]
            st.sidebar.write("搜尋結果：", match[['name', 'role']])

        # 5. 渲染圖表 (增加高度以容納 100 多人)
        st_echarts(options=options, height="800px")
        
        st.success(f"✅ 已成功載入 {len(df)} 位成員資料")

except Exception as e:
    st.error(f"檔案讀取失敗: {e}")
    st.info("請確認上傳的 CSV 編碼是否為 UTF-8，且包含 name, parent, role 欄位。")
