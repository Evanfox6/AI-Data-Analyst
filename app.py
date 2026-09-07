import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI Data Analyst Assistant", page_icon="📊", layout="wide")


def money(v):
    return f"${v:,.2f}" if pd.notna(v) else "$0.00"


def detect_columns(df):
    found = {"sales": None, "quantity": None, "product": None, "region": None, "date": None, "customer": None}
    rules = {
        "sales": ["sales", "revenue", "amount", "total sales"],
        "quantity": ["quantity", "qty", "units"],
        "product": ["product", "item"],
        "region": ["region", "area", "city"],
        "date": ["date", "time", "timestamp"],
        "customer": ["customer", "client", "buyer", "customer_id", "client_id", "user_id", "email"],
    }
    for col in df.columns:
        name = str(col).lower().strip()
        for key, words in rules.items():
            if found[key] is None and any(word in name for word in words):
                found[key] = col
    return found


def monthly(data, sales, date):
    if not sales or not date or data.empty:
        return pd.Series(dtype=float)
    x = data.dropna(subset=[date]).copy()
    if x.empty:
        return pd.Series(dtype=float)
    x["Period"] = x[date].dt.to_period("M").astype(str)
    return x.groupby("Period")[sales].sum().sort_index()


def analyst_answer(q, data, c, growth, current, previous, customer_summary=None):
    q = str(q).lower().strip()
    if data.empty:
        return "⚠️ ماكو بيانات بعد الفلترة حتى أگدر أحللها."

    sales, qty, product, region, date, customer = c.values()
    s = pd.to_numeric(data[sales], errors="coerce") if sales else pd.Series(dtype=float)

    def has(*words):
        return any(w in q for w in words)

    # 💰 Sales / Revenue
    if sales and has("total sales", "sales total", "total revenue", "revenue", "sales", "اجمالي المبيعات", "إجمالي المبيعات", "المبيعات الكلية", "المبيعات", "الإيرادات", "الايرادات", "شكد بعنا", "شكد المبيعات", "كم بعنا"):
        return f"💰 **إجمالي المبيعات:** {money(s.sum())}\n\n📋 السجلات: **{len(data):,}**"

    # 🏆 Best product
    if sales and product and has("best product", "top product", "highest product", "best item", "top item", "افضل منتج", "أفضل منتج", "اعلى منتج", "أعلى منتج", "اكثر منتج", "أكثر منتج", "المنتج الاكثر", "المنتج الأكثر", "شنو احسن منتج", "شنو أحسن منتج"):
        r = data.groupby(product)[sales].sum().sort_values(ascending=False)
        if not r.empty:
            return f"🏆 **أفضل منتج هو {r.index[0]}**\n\nحقق مبيعات بقيمة **{money(r.iloc[0])}**."

    # 🌍 Best region
    if sales and region and has("best region", "top region", "highest region", "best area", "افضل منطقة", "أفضل منطقة", "اعلى منطقة", "أعلى منطقة", "اكثر منطقة", "أكثر منطقة", "احسن منطقة", "أحسن منطقة", "وين المبيعات أعلى", "وين المبيعات اعلى"):
        r = data.groupby(region)[sales].sum().sort_values(ascending=False)
        if not r.empty:
            return f"🌍 **أفضل منطقة هي {r.index[0]}**\n\nحققت مبيعات بقيمة **{money(r.iloc[0])}**."

    # 👑 Best customer
    if customer_summary is not None and has("best customer", "top customer", "highest customer", "best client", "top client", "افضل عميل", "أفضل عميل", "اعلى عميل", "أعلى عميل", "اكثر عميل", "أكثر عميل", "افضل زبون", "أفضل زبون", "اكثر زبون", "أكثر زبون", "منو احسن عميل", "منو أحسن عميل", "منو أكثر زبون", "منو اكثر زبون"):
        r = customer_summary.sort_values("CLV", ascending=False)
        if not r.empty:
            return f"👑 **أفضل عميل هو {r.iloc[0]['Customer']}**\n\nقيمة العميل التاريخية CLV: **{money(r.iloc[0]['CLV'])}**."

    # 💎 Customer segments
    if customer_summary is not None and has("high value", "high-value", "vip customers", "valuable customers", "العملاء المميزين", "العملاء المهمين", "عملاء high", "عملاء هاي", "العملاء العاليين"):
        n = int((customer_summary["Segment"] == "High Value").sum())
        return f"💎 عدد عملاء **High Value** الحاليين: **{n}**."

    if customer_summary is not None and has("low value", "low-value", "العملاء الضعاف", "عملاء low", "عملاء لو", "العملاء الاقل", "العملاء الأقل"):
        n = int((customer_summary["Segment"] == "Low Value").sum())
        return f"🔵 عدد عملاء **Low Value** الحاليين: **{n}**."

    # 📦 Quantity
    if qty and has("quantity", "units", "qty", "total quantity", "الكمية", "الكميات", "الوحدات", "شكد الكمية", "كم وحدة", "عدد الوحدات"):
        total = pd.to_numeric(data[qty], errors="coerce").sum()
        return f"📦 **إجمالي الكمية:** {total:,.0f}"

    # 📊 Average sale
    if sales and has("average sale", "average sales", "avg sale", "average order", "aov", "متوسط البيع", "متوسط المبيعات", "متوسط الطلب", "متوسط قيمة البيع"):
        return f"📊 **متوسط قيمة البيع:** {money(s.mean())}"

    # 📈 Growth
    if has("growth", "growth rate", "increase", "decrease", "نمو", "نسبة النمو", "النمو", "زادت المبيعات", "نزلت المبيعات", "صعدت المبيعات", "المبيعات صعدت", "المبيعات نزلت", "المبيعات زادت", "المبيعات قلت", "مقارنة بالشهر السابق"):
        if growth is None:
            return "⚠️ أحتاج Date column وفترتين شهريتين على الأقل حتى أحسب النمو."
        direction = "ارتفاع" if growth > 0 else "انخفاض" if growth < 0 else "استقرار"
        return f"📈 **نسبة النمو:** {growth:.1f}%\n\nالحالة: **{direction}**\n\nالحالي: **{money(current)}**\n\nالسابق: **{money(previous)}**"

    # 🔎 Why sales dropped
    if sales and date and has("why sales dropped", "why sales decreased", "sales dropped", "sales decreased", "why did sales drop", "ليش المبيعات نزلت", "ليش المبيعات انخفضت", "ليش المبيعات قلت", "ليش المبيعات تراجعت", "سبب انخفاض المبيعات", "سبب نزول المبيعات", "سبب تراجع المبيعات", "انخفضت المبيعات", "نزلت المبيعات", "تراجعت المبيعات"):
        m = monthly(data, sales, date)
        if len(m) < 2:
            return "⚠️ أحتاج شهرين مختلفين على الأقل حتى أحلل سبب الانخفاض."
        p, cur = m.iloc[-2], m.iloc[-1]
        ch = ((cur - p) / p * 100) if p else 0
        ans = f"🔎 **تحليل التغير**\n\nالسابق: **{money(p)}**\n\nالحالي: **{money(cur)}**\n\nالتغير: **{ch:.1f}%**\n\n"
        if product:
            r = data.groupby(product)[sales].sum().sort_values()
            if not r.empty:
                ans += f"📉 أضعف منتج حالياً: **{r.index[0]}** — {money(r.iloc[0])}.\n\n"
        if region:
            r = data.groupby(region)[sales].sum().sort_values()
            if not r.empty:
                ans += f"🌍 أضعف منطقة حالياً: **{r.index[0]}** — {money(r.iloc[0])}."
        return ans

    # 📊 Sales by product
    if sales and product and has("sales by product", "products sales", "product sales", "مبيعات المنتجات", "المبيعات حسب المنتج", "المبيعات للمنتجات", "كل منتج شكد"):
        r = data.groupby(product)[sales].sum().sort_values(ascending=False).head(10)
        return "🏆 **المبيعات حسب المنتج:**\n\n" + "\n".join(f"• **{k}** — {money(v)}" for k, v in r.items())

    # 🌍 Sales by region
    if sales and region and has("sales by region", "regions sales", "region sales", "مبيعات المناطق", "المبيعات حسب المنطقة", "كل منطقة شكد"):
        r = data.groupby(region)[sales].sum().sort_values(ascending=False)
        return "🌍 **المبيعات حسب المنطقة:**\n\n" + "\n".join(f"• **{k}** — {money(v)}" for k, v in r.items())

    # 📋 Summary
    if has("summary", "overview", "summarize", "ملخص", "ملخص البيانات", "لخص", "لخّص", "اختصر البيانات", "شنو وضع البيانات", "اعطني ملخص", "أعطني ملخص"):
        ans = "📋 **ملخص البيانات الحالية**\n\n"
        if sales:
            ans += f"💰 المبيعات: **{money(s.sum())}**\n\n"
        if qty:
            ans += f"📦 الكمية: **{pd.to_numeric(data[qty], errors='coerce').sum():,.0f}**\n\n"
        ans += f"🧾 السجلات: **{len(data):,}**\n\n"
        if customer_summary is not None and not customer_summary.empty:
            ans += f"👥 العملاء: **{len(customer_summary):,}**\n\n"
            ans += f"👑 أفضل عميل: **{customer_summary.iloc[0]['Customer']}**\n\n"
        if product and sales:
            r = data.groupby(product)[sales].sum().sort_values(ascending=False)
            if not r.empty:
                ans += f"🏆 أفضل منتج: **{r.index[0]}**\n\n"
        if region and sales:
            r = data.groupby(region)[sales].sum().sort_values(ascending=False)
            if not r.empty:
                ans += f"🌍 أفضل منطقة: **{r.index[0]}**"
        return ans

    return ("🤖 أگدر أجاوبك على أسئلة مثل:\n\n"
            "• **شنو إجمالي المبيعات؟**\n"
            "• **شكد بعنا؟**\n"
            "• **شنو أفضل منتج؟**\n"
            "• **شنو أكثر منتج مبيعاً؟**\n"
            "• **شنو أفضل منطقة؟**\n"
            "• **وين المبيعات أعلى؟**\n"
            "• **منو أفضل عميل؟**\n"
            "• **منو أكثر زبون دافع؟**\n"
            "• **شنو عدد عملاء High Value؟**\n"
            "• **ليش المبيعات نزلت؟**\n"
            "• **شنو نسبة النمو؟**\n"
            "• **المبيعات حسب المنتج**\n"
            "• **المبيعات حسب المنطقة**\n"
            "• **أعطني ملخص البيانات**")


st.title("📊 AI Data Analyst Assistant")
st.write("Upload your sales data and get automatic KPIs, growth analysis, charts, customer value analysis, and an interactive AI analyst.")

uploaded_file = st.file_uploader("📁 Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is None:
    st.info("👆 Upload a CSV or Excel file to start.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.lower().endswith(".csv") else pd.read_excel(uploaded_file)
    st.success(f"✅ Loaded: {uploaded_file.name}")
    df.columns = [str(x).strip() for x in df.columns]
    original_rows = len(df)
    df = df.drop_duplicates().copy()
    removed_duplicates = original_rows - len(df)
    c = detect_columns(df)

    if c["sales"]:
        df[c["sales"]] = pd.to_numeric(df[c["sales"]], errors="coerce")
    if c["quantity"]:
        df[c["quantity"]] = pd.to_numeric(df[c["quantity"]], errors="coerce")
    if c["date"]:
        df[c["date"]] = pd.to_datetime(df[c["date"]], errors="coerce")

    st.sidebar.header("🔎 Filters")
    filtered = df.copy()

    if c["product"]:
        vals = sorted(df[c["product"]].dropna().astype(str).unique())
        selected = st.sidebar.multiselect("Product", vals, default=vals)
        filtered = filtered[filtered[c["product"]].astype(str).isin(selected)]

    if c["region"]:
        vals = sorted(df[c["region"]].dropna().astype(str).unique())
        selected = st.sidebar.multiselect("Region", vals, default=vals)
        filtered = filtered[filtered[c["region"]].astype(str).isin(selected)]

    if c["customer"]:
        vals = sorted(df[c["customer"]].dropna().astype(str).str.strip().unique())
        selected = st.sidebar.multiselect("Customer", vals, default=vals)
        filtered = filtered[filtered[c["customer"]].astype(str).str.strip().isin(selected)]

    if c["date"]:
        valid_dates = df[c["date"]].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_value = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            if isinstance(date_value, tuple) and len(date_value) == 2:
                start_date, end_date = date_value
                start_ts = pd.Timestamp(start_date)
                end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)
                filtered = filtered[(filtered[c["date"]] >= start_ts) & (filtered[c["date"]] < end_ts)]

    if filtered.empty:
        st.warning("⚠️ ماكو بيانات مطابقة للفلاتر الحالية. غيّر الفلاتر حتى تظهر النتائج.")
        st.stop()

    st.subheader("📌 Dataset Overview")
    a, b, d, e = st.columns(4)
    a.metric("Rows", f"{len(filtered):,}")
    b.metric("Columns", f"{len(filtered.columns):,}")
    d.metric("Missing Values", f"{int(filtered.isna().sum().sum()):,}")
    e.metric("Duplicates Removed", f"{removed_duplicates:,}")
    st.divider()

    total_sales = filtered[c["sales"]].sum() if c["sales"] else 0
    total_qty = filtered[c["quantity"]].sum() if c["quantity"] else 0
    avg_sale = filtered[c["sales"]].mean() if c["sales"] else 0

    st.subheader("📊 Key Performance Indicators")
    a, b, d, e = st.columns(4)
    a.metric("💰 Total Sales", money(total_sales))
    b.metric("📦 Total Quantity", f"{total_qty:,.0f}")
    d.metric("🧾 Average Sale", money(avg_sale))
    e.metric("📋 Records", f"{len(filtered):,}")
    st.divider()

    growth = current = previous = None
    st.subheader("📈 Sales Analytics")

    if c["sales"] and c["date"]:
        st.markdown("### 📈 Sales Trend")
        chart_data = filtered.dropna(subset=[c["date"]]).copy()
        chart_data["Period"] = chart_data[c["date"]].dt.to_period("M").astype(str)
        monthly_df = chart_data.groupby("Period", as_index=False)[c["sales"]].sum()
        st.plotly_chart(px.line(monthly_df, x="Period", y=c["sales"], markers=True, title="Monthly Sales Trend"), width="stretch")
        if len(monthly_df) >= 2:
            previous = monthly_df[c["sales"]].iloc[-2]
            current = monthly_df[c["sales"]].iloc[-1]
            if previous != 0:
                growth = (current - previous) / previous * 100

    col1, col2 = st.columns(2)
    with col1:
        if c["sales"] and c["product"]:
            chart = filtered.groupby(c["product"], as_index=False)[c["sales"]].sum().sort_values(c["sales"], ascending=False)
            st.plotly_chart(px.bar(chart, x=c["product"], y=c["sales"], title="Sales by Product"), width="stretch")
    with col2:
        if c["sales"] and c["region"]:
            chart = filtered.groupby(c["region"], as_index=False)[c["sales"]].sum().sort_values(c["sales"], ascending=False)
            st.plotly_chart(px.bar(chart, x=c["region"], y=c["sales"], title="Sales by Region"), width="stretch")

    st.divider()
    st.subheader("🤖 Automatic Insights")
    insights = []
    if c["sales"] and c["product"]:
        r = filtered.groupby(c["product"])[c["sales"]].sum().sort_values(ascending=False)
        if not r.empty:
            insights.append(f"🏆 **Best product:** {r.index[0]} generated {money(r.iloc[0])} in sales.")
    if c["sales"] and c["region"]:
        r = filtered.groupby(c["region"])[c["sales"]].sum().sort_values(ascending=False)
        if not r.empty:
            insights.append(f"🌍 **Best region:** {r.index[0]} generated {money(r.iloc[0])} in sales.")
    if growth is not None:
        if growth > 0:
            insights.append(f"📈 Sales increased by **{growth:.1f}%** compared with the previous month.")
        elif growth < 0:
            insights.append(f"📉 Sales decreased by **{abs(growth):.1f}%** compared with the previous month.")
        else:
            insights.append("➡️ Sales remained stable compared with the previous month.")
    for item in insights:
        st.info(item)
    if not insights:
        st.warning("Not enough information to generate automatic insights.")

    st.divider()
    st.subheader("📈 Growth Analysis")
    if growth is not None:
        a, b, d = st.columns(3)
        a.metric("Monthly Growth", f"{growth:.1f}%")
        b.metric("Current Period", money(current))
        d.metric("Previous Period", money(previous))
    else:
        st.warning("Growth analysis requires a valid Date column and at least two different months.")

    st.divider()
    st.subheader("👥 Customer Value Analysis")
    st.caption("Historical CLV = total observed revenue generated by the customer in the currently filtered dataset. Segments use customer CLV quartiles.")

    customer_summary = None
    if c["customer"] and c["sales"]:
        base = filtered.dropna(subset=[c["customer"], c["sales"]]).copy()
        base["Customer"] = base[c["customer"]].astype(str).str.strip()
        base = base[base["Customer"] != ""]
        if not base.empty:
            customer_summary = base.groupby("Customer", as_index=False).agg(
                Orders=("Customer", "size"),
                Total_Sales=(c["sales"], "sum"),
                Average_Order_Value=(c["sales"], "mean"),
            )
            if c["quantity"]:
                qty = base.groupby("Customer", as_index=False)[c["quantity"]].sum().rename(columns={c["quantity"]: "Total_Quantity"})
                customer_summary = customer_summary.merge(qty, on="Customer", how="left")
            if c["date"]:
                dates = base.dropna(subset=[c["date"]]).groupby("Customer")[c["date"]].agg(First_Purchase="min", Last_Purchase="max").reset_index()
                customer_summary = customer_summary.merge(dates, on="Customer", how="left")
                customer_summary["Active_Months"] = ((customer_summary["Last_Purchase"] - customer_summary["First_Purchase"]).dt.days.div(30.4375).fillna(0).clip(lower=0).add(1).round(1))
                customer_summary["Orders_per_Month"] = (customer_summary["Orders"] / customer_summary["Active_Months"]).round(2)

            customer_summary["CLV"] = customer_summary["Total_Sales"]
            q25 = customer_summary["CLV"].quantile(0.25)
            q75 = customer_summary["CLV"].quantile(0.75)
            if q25 == q75:
                customer_summary["Segment"] = "Mid Value"
            else:
                customer_summary["Segment"] = customer_summary["CLV"].apply(lambda v: "High Value" if v >= q75 else ("Low Value" if v <= q25 else "Mid Value"))
            customer_summary = customer_summary.sort_values("CLV", ascending=False)

            high = int((customer_summary["Segment"] == "High Value").sum())
            mid = int((customer_summary["Segment"] == "Mid Value").sum())
            low = int((customer_summary["Segment"] == "Low Value").sum())
            a, b, d, e = st.columns(4)
            a.metric("👤 Customers", f"{len(customer_summary):,}")
            b.metric("💎 High Value", f"{high:,}")
            d.metric("🟡 Mid Value", f"{mid:,}")
            e.metric("🔵 Low Value", f"{low:,}")

            display_cols = ["Customer", "Segment", "Orders", "Total_Sales", "Average_Order_Value", "CLV"]
            if c["quantity"]:
                display_cols.insert(4, "Total_Quantity")
            if c["date"]:
                display_cols += ["First_Purchase", "Last_Purchase", "Active_Months", "Orders_per_Month"]
            table = customer_summary[display_cols].rename(columns={
                "Total_Sales": "Total Sales", "Average_Order_Value": "Avg Order Value", "Total_Quantity": "Total Quantity",
                "First_Purchase": "First Purchase", "Last_Purchase": "Last Purchase", "Active_Months": "Active Months", "Orders_per_Month": "Orders / Month"
            })
            st.markdown("### 🎯 Customer Segments")
            st.dataframe(table, width="stretch", hide_index=True, column_config={
                "Total Sales": st.column_config.NumberColumn("Total Sales", format="$%.2f"),
                "Avg Order Value": st.column_config.NumberColumn("Avg Order Value", format="$%.2f"),
                "CLV": st.column_config.NumberColumn("CLV", format="$%.2f"),
            })

            st.markdown("### 💰 CLV Distribution")
            clv_chart = px.bar(customer_summary.head(20), x="Customer", y="CLV", color="Segment", title="Top Customers by Historical CLV", labels={"CLV": "Customer Lifetime Value"})
            st.plotly_chart(clv_chart, width="stretch")
            st.info("💡 True forward-looking CLV normally needs retention/churn, gross margin, and expected customer lifetime. This dashboard uses historical revenue as the CLV measure available from the uploaded data.")
        else:
            st.warning("No valid customer records are available after the current filters.")
    else:
        st.warning("Customer analysis needs a Customer/Client/Buyer/Customer ID column and a Sales/Revenue/Amount column.")

    st.divider()
    st.subheader("📥 Export Report")
    st.caption("نزّل البيانات والتحليلات الحالية حسب الفلاتر المطبقة.")

    report_rows = {
        "Metric": ["Total Sales", "Total Quantity", "Average Sale", "Records", "Monthly Growth", "Current Period", "Previous Period"],
        "Value": [
            total_sales,
            total_qty,
            avg_sale,
            len(filtered),
            growth if growth is not None else None,
            current if current is not None else None,
            previous if previous is not None else None,
        ],
    }
    report_kpis = pd.DataFrame(report_rows)

    import io
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        report_kpis.to_excel(writer, sheet_name="KPIs", index=False)
        filtered.to_excel(writer, sheet_name="Filtered Data", index=False)
        if customer_summary is not None and not customer_summary.empty:
            customer_summary.to_excel(writer, sheet_name="Customers", index=False)
        if c["product"] and c["sales"]:
            filtered.groupby(c["product"])[c["sales"]].sum().sort_values(ascending=False).reset_index().to_excel(writer, sheet_name="Sales by Product", index=False)
        if c["region"] and c["sales"]:
            filtered.groupby(c["region"])[c["sales"]].sum().sort_values(ascending=False).reset_index().to_excel(writer, sheet_name="Sales by Region", index=False)

    st.download_button(
        "📥 Download Excel Report",
        data=excel_buffer.getvalue(),
        file_name="AI_Data_Analyst_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

    st.divider()
    st.subheader("🔎 Data Preview")
    st.dataframe(filtered.head(100), width="stretch")

    with st.expander("🧠 Detected Columns"):
        st.write(f"**Sales:** {c['sales']}")
        st.write(f"**Quantity:** {c['quantity']}")
        st.write(f"**Product:** {c['product']}")
        st.write(f"**Region:** {c['region']}")
        st.write(f"**Date:** {c['date']}")
        st.write(f"**Customer:** {c['customer']}")

    # =====================================================
    # AI IS INTENTIONALLY THE LAST SECTION
    # =====================================================
    st.divider()
    st.subheader("🤖 AI Data Analyst")
    st.caption("💡 اسألني عن البيانات الحالية بعد تطبيق كل الفلاتر.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 أهلاً! اسألني عن البيانات الحالية، مثلاً: **ليش المبيعات انخفضت؟** أو **شنو أفضل عميل؟**"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.markdown("### 💡 أسئلة جاهزة")
    st.caption("اضغط على أي سؤال حتى أجاوبك مباشرة، أو اكتب سؤالك بنفسك.")
    example_questions = [
        "شنو إجمالي المبيعات؟",
        "شنو أفضل منتج؟",
        "منو أفضل عميل؟",
        "وين المبيعات أعلى؟",
        "شنو نسبة النمو؟",
        "ليش المبيعات نزلت؟",
    ]
    cols = st.columns(3)
    for i, example in enumerate(example_questions):
        with cols[i % 3]:
            if st.button(example, key=f"ai_example_{i}", width="stretch"):
                st.session_state.pending_ai_question = example

    question = st.chat_input("🤖 اكتب سؤالك عن البيانات...")
    question = question or st.session_state.pop("pending_ai_question", None)
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        answer = analyst_answer(question, filtered, c, growth, current, previous, customer_summary)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

except Exception as error:
    st.error(f"❌ Something went wrong: {error}")
