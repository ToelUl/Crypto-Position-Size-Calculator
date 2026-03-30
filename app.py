import streamlit as st
import math
import pandas as pd

# ==========================================
# Parameters & Data Mapping
# ==========================================

# Fee Rates Table (Maker_Spot, Taker_Spot, Maker_Futures, Taker_Futures)
FEE_RATES = {
    "Binance": {"Spot": {"Maker": 0.00100, "Taker": 0.00100}, "USDT-M": {"Maker": 0.00020, "Taker": 0.00050}},
    "OKX": {"Spot": {"Maker": 0.00080, "Taker": 0.00100}, "USDT-M": {"Maker": 0.00020, "Taker": 0.00050}},
    "Bitget": {"Spot": {"Maker": 0.00100, "Taker": 0.00100}, "USDT-M": {"Maker": 0.00020, "Taker": 0.00060}},
    "Bybit": {"Spot": {"Maker": 0.00100, "Taker": 0.00100}, "USDT-M": {"Maker": 0.00020, "Taker": 0.00055}},
    "Hyperliquid": {"Spot": {"Maker": 0.00070, "Taker": 0.00070}, "USDT-M": {"Maker": 0.00010, "Taker": 0.00045}},
    "Pionex": {"Spot": {"Maker": 0.00050, "Taker": 0.00050}, "USDT-M": {"Maker": 0.00020, "Taker": 0.00050}},
}

# Standard Maintenance Margin Rate (MMR) for basic tiers (0.4%)
DEFAULT_MMR = 0.004

# Order quantity precision by coin (decimal places)
COIN_PRECISION = {
    'BTC': 3, 'ETH': 3, 'BNB': 2, 'SOL': 1, 'XRP': 0, 'DOGE': 0,
    'ADA': 0, 'SHIB': 0, 'AVAX': 1, 'DOT': 1, 'TRX': 0, 'LTC': 2,
    'MAC': 0, 'BCH': 3, 'LINK': 2, 'ATOM': 2, 'UNI': 2, 'ICP': 2,
    'APT': 1, 'OP': 1, 'ARB': 1, 'SUI': 1, 'SEI': 1, 'TIA': 1,
    'WLD': 1, 'FET': 1, 'RNDR': 1, 'PEPE': 0, 'BONK': 0, 'WIF': 0, 'FLOKI': 0
}


# ==========================================
# Helper Functions
# ==========================================

def get_coin_decimals(coin_symbol, unit_price):
    """Get the minimum order decimal places (precision) for the asset."""
    coin_symbol = coin_symbol.upper().strip()
    if coin_symbol in COIN_PRECISION:
        return COIN_PRECISION[coin_symbol]

    if unit_price >= 1000:
        return 3
    elif unit_price >= 50:
        return 2
    elif unit_price >= 1:
        return 1
    else:
        return 0


def truncate_amount(amount, decimals):
    """Floor rounding to match exchange precision and prevent exceeding max risk."""
    if decimals <= 0:
        return float(math.floor(amount))
    factor = 10.0 ** decimals
    return math.floor(amount * factor) / factor


# ==========================================
# Main Application Logic
# ==========================================

st.set_page_config(page_title="Pro Position Size Calculator", layout="wide", page_icon="📈")

# Sidebar Input Panel
with st.sidebar:
    st.header("⚡ Trading Parameters")

    exchange = st.selectbox("1. Exchange", list(FEE_RATES.keys()), index=0)
    market_type = st.radio("2. Market Type", ["Spot", "USDT-M Futures (Isolated)"], index=1)
    market_key = "Spot" if "Spot" in market_type else "USDT-M"

    entry_type = st.radio("3. Entry Order Type", ["Taker (Market)", "Maker (Limit)"], index=0)
    entry_key = "Taker" if "Taker" in entry_type else "Maker"

    coin_symbol = st.text_input("4. Ticker / Symbol", value="BTC")
    account_value = st.number_input("5. Total Account Balance (USDT)", value=10000.0, min_value=1.0, step=100.0)

    entry_price = st.number_input("6. Entry Price", value=65000.0, format="%.4f")
    stop_loss = st.number_input("7. Stop Loss Price", value=63000.0, format="%.4f")
    take_profit = st.number_input("8. Take Profit Price (Maker)", value=75000.0, format="%.4f")

    leverage = st.slider("9. Leverage", min_value=1, max_value=125, value=10, step=1)
    if market_key == "Spot" and leverage > 1:
        st.warning("Spot market leverage is 1x. Calculations will assume no liquidation.")

    risk_pct = st.slider("10. Max Risk per Trade (%)", min_value=0.1, max_value=100.0, value=1.0, step=0.1)
    slippage_pct = st.number_input("11. Estimated SL Slippage (%)", value=0.1, min_value=0.0, max_value=5.0, step=0.05)

    win_rate_pct = st.slider("12. Estimated Win Rate (%)", min_value=1.0, max_value=100.0, value=30.0, step=1.0)

    calculate_btn = st.button("🚀 Calculate Position", type="primary", use_container_width=True)

# Main Result Panel
st.title("📊 Professional Position Report")

# ==========================================
# Beginner's Guide & Glossary (新手友善區)
# ==========================================
with st.expander("📖 Beginner's Guide & Glossary (新手必看：操作指南與名詞解釋)", expanded=False):
    # Language Toggle
    guide_lang = st.radio("Language / 語言", ["English", "繁體中文"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if guide_lang == "繁體中文":
        st.markdown("""
        ### 🎯 操作指南
        1. **設定基礎資訊 (1-4)**：在左側選擇你的交易所、市場類型（現貨 Spot 還是合約 USDT-M），以及你要交易的幣種代號。
        2. **輸入資金與價格 (5-8)**：填入你的總資金 (Account Balance)，並輸入你規劃好的進場價 (Entry)、停損價 (Stop Loss) 與停利價 (Take Profit)。
        3. **設定風險控管 (9-11)**：設定你想使用的槓桿倍數 (Leverage)，以及你這筆交易「最多願意虧損總資金的百分之幾」(Max Risk per Trade，新手強烈建議設在 1%~2%)。
        4. **一鍵計算**：設定好預估勝率後，點擊左下方「🚀 Calculate Position」，右側就會告訴你**應該買入多少合約數量**、**需要準備多少保證金**，以及這筆交易值不值得做。

        ### 📚 核心名詞解釋
        *   **Maker (掛單) / Taker (吃單)**：
            *   **Maker**：指定一個價格排隊等成交（通常是限價單 Limit），能幫交易所提供流動性，手續費較低甚至為負。
            *   **Taker**：直接用當下市場最好的價格馬上成交（通常是市價單 Market），手續費較高。
        *   **Leverage (槓桿)**：向交易所借錢放大你的交易規模。**請注意：在本計算機中，提高槓桿「不會」增加你的虧損金額**（因為系統會自動依據你的 Risk % 調整倉位），提高槓桿只會減少你開倉所需要的本金（起始保證金）。
        *   **Slippage (滑點)**：當停損觸發時，實際成交的價格通常會比你設定的停損價還要差一點，這就叫滑點。把滑點考慮進去，風險計算才會精準。
        *   **Notional Position Size (名目價值/總倉位大小)**：這筆交易「真正」的總價值。例如你拿 100 U 開 10 倍槓桿，名目價值就是 1,000 U。
        *   **Initial Margin (起始保證金)**：你實際上需要從帳戶餘額裡拿出來開倉的現金。
        *   **Net Risk:Reward Ratio (淨盈虧比)**：扣除手續費與滑點後，你的「獲利空間」與「虧損風險」的比例。例如 2 : 1 代表：你看錯賠 1 塊錢，看對可以賺 2 塊錢。
        *   **Expectancy (期望值)**：結合你的「預估勝率」與「盈虧比」，計算出你**平均做一次這筆交易能賺多少個風險單位的錢**。若期望值小於 0（呈現紅色警告），代表這是一個長期會賠錢的策略，建議重新調整進出場點位！
        """)
    else:
        st.markdown("""
        ### 🎯 How to Use
        1. **Basic Setup (1-4)**: Select your Exchange, Market Type (Spot or USDT-M Futures), and the Ticker/Symbol of the coin you want to trade on the left sidebar.
        2. **Capital & Prices (5-8)**: Enter your Total Account Balance, followed by your planned Entry Price, Stop Loss Price, and Take Profit Price.
        3. **Risk Management (9-11)**: Set your Leverage and the Maximum Risk per Trade % (It is highly recommended for beginners to risk only 1%~2% of total capital per trade).
        4. **Calculate**: After setting your estimated Win Rate, click "🚀 Calculate Position". The report on the right will show you **exactly how many contracts to buy**, the **margin required**, and whether the trade setup is mathematically sound.

        ### 📚 Glossary
        *   **Maker / Taker**:
            *   **Maker**: Placing an order that doesn't fill immediately (usually Limit orders), adding liquidity to the order book. Fees are generally lower.
            *   **Taker**: Placing an order that fills immediately against existing orders (usually Market orders), taking liquidity. Fees are generally higher.
        *   **Leverage**: Borrowing capital from the exchange to increase your position size. **Note: In this calculator, increasing leverage does NOT increase your total risk amount** (the system auto-adjusts your position size based on your Risk %). Higher leverage only reduces the Initial Margin required to open the trade.
        *   **Slippage**: The difference between your expected Stop Loss price and the actual execution price. Factoring this in makes risk calculation far more accurate.
        *   **Notional Position Size**: The true total value of your position. (e.g., \$100 margin x 10x leverage = \$1,000 notional size).
        *   **Initial Margin**: The actual cash needed from your account balance to open the position.
        *   **Net Risk:Reward Ratio**: The ratio of your potential profit to your potential loss, *after* accounting for fees and slippage. For example, 2 : 1 means you risk \$1 to potentially make \$2.
        *   **Expectancy**: Combines your Estimated Win Rate and Risk:Reward Ratio to calculate **how much you can expect to earn on average per trade (in Risk multiples)**. If this is below 0 (shows a red warning), it's a losing strategy long-term, and you should adjust your entry/exit levels!
        """)

if calculate_btn:
    # 1. Basic Logic Validation
    if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
        st.error("❌ Price fields cannot be 0 or negative.")
        st.stop()

    if entry_price == stop_loss:
        st.error("❌ Critical Error: Stop Loss price cannot equal Entry Price.")
        st.stop()

    # 2. Determine Direction & Validate TP Logic
    direction = "Long" if stop_loss < entry_price else "Short"
    direction_text = "Long ▲" if direction == "Long" else "Short ▼"

    if direction == "Long" and take_profit <= entry_price:
        st.error("❌ Logic Error: For a Long position, Take Profit must be strictly greater than Entry Price.")
        st.stop()
    if direction == "Short" and take_profit >= entry_price:
        st.error("❌ Logic Error: For a Short position, Take Profit must be strictly less than Entry Price.")
        st.stop()

    # 3. Liquidation Price Estimation (Isolated Margin + MMR)
    if market_key == "Spot":
        liquidation_price = 0.0
    else:
        if direction == "Long":
            # Long Liquidation: Entry * (1 - 1/Leverage + MMR)
            liquidation_price = entry_price * (1 - (1 / leverage) + DEFAULT_MMR)
        else:
            # Short Liquidation: Entry * (1 + 1/Leverage - MMR)
            liquidation_price = entry_price * (1 + (1 / leverage) - DEFAULT_MMR)

    # 4. Distance and Asymmetric Friction Cost Calculation
    if direction == "Long":
        sl_distance = (entry_price - stop_loss) / entry_price
        tp_distance = (take_profit - entry_price) / entry_price
    else:
        sl_distance = (stop_loss - entry_price) / entry_price
        tp_distance = (entry_price - take_profit) / entry_price

    entry_fee_rate = FEE_RATES[exchange][market_key][entry_key]
    sl_exit_fee_rate = FEE_RATES[exchange][market_key]["Taker"]
    tp_exit_fee_rate = FEE_RATES[exchange][market_key]["Maker"]  # Assuming TP is a Limit order

    # SL is usually a market order: Entry Fee + SL Taker Fee + Slippage
    total_sl_friction = entry_fee_rate + sl_exit_fee_rate + (slippage_pct / 100.0)
    actual_sl_cost = sl_distance + total_sl_friction

    # 5. Risk and Position Sizing
    max_risk_amount = account_value * (risk_pct / 100.0)

    if actual_sl_cost <= 0:
        st.error("❌ Error: Invalid SL distance or slippage settings.")
        st.stop()

    notional_position_size = max_risk_amount / actual_sl_cost
    initial_margin = notional_position_size / leverage if market_key != "Spot" else notional_position_size

    raw_amount = notional_position_size / entry_price
    coin_dec = get_coin_decimals(coin_symbol, entry_price)
    contract_quantity = truncate_amount(raw_amount, coin_dec)

    # Recalculate true notional based on truncated quantity
    true_notional = contract_quantity * entry_price

    # 6. Expected PnL & RR Calculation
    # TP friction: Entry Fee + TP Maker Fee (No slippage assumed for Limit TP)
    expected_profit = true_notional * (tp_distance - entry_fee_rate - tp_exit_fee_rate)
    if expected_profit < 0:
        expected_profit = 0

        # Recalculate true risk based on truncated quantity
    true_risk = true_notional * actual_sl_cost
    rr_ratio = expected_profit / true_risk if true_risk > 0 else 0

    # 7. Expectancy Calculation
    win_rate = win_rate_pct / 100.0
    loss_rate = 1.0 - win_rate
    expectancy = (win_rate * rr_ratio) - (loss_rate * 1)

    # ==========================
    # Risk Alerts
    # ==========================
    st.subheader("🛡️ Real-time Risk Feedback")

    alerts = []
    if market_key != "Spot":
        if (direction == "Long" and stop_loss <= liquidation_price) or \
                (direction == "Short" and stop_loss >= liquidation_price):
            st.error(
                f"💀 FATAL ERROR: Stop Loss is beyond the Estimated Liquidation Price ({liquidation_price:.4f}). You will be liquidated before SL triggers. Lower your leverage or tighten your SL.")
            st.stop()

    if initial_margin > account_value:
        alerts.append({"type": "error", "msg": "❌ Initial Margin exceeds balance. Reduce risk % or increase leverage."})
    if sl_distance < total_sl_friction:
        alerts.append(
            {"type": "error", "msg": "❌ SL too tight. Fees and slippage will consume the entire price movement."})

    if expectancy <= 0:
        min_rr_needed = loss_rate / win_rate if win_rate > 0 else float('inf')
        alerts.append({
            "type": "error",
            "msg": f"❌ Negative Expectancy ({expectancy:.2f} R). At {win_rate_pct}% win rate, you need at least {min_rr_needed:.2f} RR to break even (Current: {rr_ratio:.2f})."
        })
    elif expectancy < 0.2:
        alerts.append({
            "type": "warning",
            "msg": f"⚠️ Low Expectancy ({expectancy:.2f} R). While positive, there is little room for error. Manage slippage strictly."
        })

    if len(alerts) == 0:
        if initial_margin > account_value * 0.3:
            alerts.append(
                {"type": "warning", "msg": "⚠️ Initial Margin usage > 30%. Watch out for concentration risk."})
        if coin_symbol.upper() not in ["BTC", "ETH", "SOL", "BNB"] and slippage_pct < 0.2:
            alerts.append({"type": "warning",
                           "msg": "⚠️ Mid/Low-cap coin detected. Consider increasing slippage for realistic results."})

    if len(alerts) > 0:
        for alert in alerts:
            if alert["type"] == "error":
                st.error(alert["msg"])
            else:
                st.warning(alert["msg"])
    else:
        st.success("✅ Risk assessment passed. Expectancy is healthy and parameters are logical.")

    # ==========================
    # Results Display
    # ==========================
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Direction**: {direction_text}")
    with c2:
        st.markdown(f"**Asset**: {coin_symbol.upper()}")
    with c3:
        st.markdown(f"**Mode**: {market_key} ({exchange} | {leverage}x)")

    st.markdown("<br>", unsafe_allow_html=True)

    results_data = {
        "Metric": [
            "Total Balance",
            "Max Risk Amount (1R)",
            "Stop Loss Distance",
            "Est. Liquidation Price",
            "**Notional Position Size**",
            "**Initial Margin (IM)**",
            "**Contract Quantity**",
            "Est. Average Win Rate",
            "Projected PnL",
            "**Net Risk:Reward Ratio**",
            "**Expectancy (Per Trade)**"
        ],
        "Value": [
            f"{account_value:,.2f} USDT",
            f"{max_risk_amount:,.2f} USDT ({risk_pct:.2f}%)",
            f"{sl_distance * 100:.2f}% (Actual: {actual_sl_cost * 100:.2f}% incl. friction)",
            f"{liquidation_price:,.4f}" if liquidation_price > 0 else "N/A (Spot)",
            f"**{true_notional:,.2f} USDT**",
            f"**{initial_margin:,.2f} USDT**",
            f"**{contract_quantity:,.{coin_dec}f} {coin_symbol.upper()}**",
            f"{win_rate_pct:.1f}%",
            f"{expected_profit:,.2f} USDT",
            f"**{rr_ratio:.2f} : 1**",
            f"**{expectancy:.2f} R**"
        ]
    }

    st.table(pd.DataFrame(results_data))

else:
    st.info("Adjust parameters in the sidebar and click '🚀 Calculate Position'.")

