# =============================================================================
# config.py — CHỈNH FILE NÀY TRƯỚC KHI CHẠY APP
# =============================================================================
# Chỉ cần sửa 1 dòng ở Bước 1.
# Bước 2 chỉ cần chỉnh nếu Column Check báo MISSING.
# =============================================================================

# ── BƯỚC 1: Đường dẫn thư mục chứa ALL_BCTC_*.xlsx ──────────────────────────
# Default '.' = cùng thư mục với file này — không cần sửa nếu đặt đúng folder.
RAW_EXCEL_DIR = "."

# ── Sheet name (không cần sửa) ────────────────────────────────────────────────
RAW_SHEET = "TONG_HOP"

# =============================================================================
# BƯỚC 2: Column mapping — tên cột thật trong TONG_HOP
# =============================================================================
# NOTE: Mapping này dùng cho doanh nghiệp phi tài chính (standard VAS format).
# Ngân hàng / chứng khoán / bảo hiểm dùng format BCTC khác → các chỉ số sẽ
# hiện "-" cho những ngành đó — đây là expected behavior, không phải lỗi.
#
# Nếu cần sửa: chạy lệnh này để xem tên cột thật:
#   py -c "import pandas as pd, glob, os
#   f = sorted(glob.glob('ALL_BCTC_*.xlsx'))[-1]
#   print(pd.read_excel(f, sheet_name='TONG_HOP', nrows=0).columns.tolist())"
# =============================================================================

# ── Identity columns ──────────────────────────────────────────────────────────
COL_TICKER   = "ticker"
COL_EXCHANGE = "exchange"
COL_YEAR     = "year"
COL_QUARTER  = "quarter"
COL_INDUSTRY = "industry"   # added from SSI export

# ── Income Statement ──────────────────────────────────────────────────────────
# Doanh thu thuần (non-financial standard VAS)
COL_REVENUE    = "3. Doanh thu thuần về bán hàng và cung cấp dịch vụ"

# Giá vốn hàng bán — note: trailing space in source data
COL_COGS       = "4. Giá vốn hàng bán "

# Lợi nhuận gộp
COL_GROSS      = "5. Lợi nhuận gộp về bán hàng và cung cấp dịch vụ"

# Lợi nhuận thuần từ HĐKD (EBIT proxy — before financial income/expense)
COL_EBIT       = "11. Lợi nhuận thuần từ hoạt động kinh doanh"

# Chi phí lãi vay (nằm trong mục "Chi phí tài chính")
COL_INT_EXP    = "   Trong đó: Chi phí đi vay"

# Lợi nhuận sau thuế
COL_NET_PROFIT = "18. Lợi nhuận sau thuế thu nhập doanh nghiệp"

# Lợi nhuận trước thuế — dùng để tính effective tax rate cho ROIC
COL_EBT        = "15. Tổng lợi nhuận kế toán trước thuế"

# Chi phí thuế TNDN hiện hành — dùng cho effective tax rate
# (không cộng thêm deferred tax để tránh distortion)
COL_TAX        = "16. Chi phí thuế TNDN hiện hành"

# Khấu hao — nằm trong phần điều chỉnh của LCTT (note: leading space)
COL_DA         = " Khấu hao TSCĐ và BĐSĐT"

# ── Balance Sheet ─────────────────────────────────────────────────────────────
# Tổng tài sản
COL_TOTAL_ASSETS = "TỔNG CỘNG TÀI SẢN"

# Tài sản ngắn hạn (aggregate line A)
COL_CUR_ASSETS   = "A. TÀI SẢN NGẮN HẠN"

# Tiền và tương đương tiền
COL_CASH         = "I. Tiền và các khoản tương đương tiền"

# Phải thu ngắn hạn (aggregate)
COL_RECEIVABLES  = "III. Các khoản phải thu ngắn hạn"

# Hàng tồn kho (aggregate)
COL_INVENTORY    = "IV. Hàng tồn kho"

# Nợ ngắn hạn (aggregate)
COL_CUR_LIAB     = "I. Nợ ngắn hạn"

# Vay và nợ thuê tài chính ngắn hạn
COL_ST_DEBT      = "11. Vay và nợ thuê tài chính ngắn hạn"

# Vay và nợ thuê tài chính dài hạn
COL_LT_DEBT      = "9. Vay và nợ thuê tài chính dài hạn"

# Vốn chủ sở hữu (aggregate)
COL_EQUITY       = "D. VỐN CHỦ SỞ HỮU"

# Tài sản cố định (aggregate — dùng cho Collateral Coverage)
COL_FIXED_ASSETS = "II. Tài sản cố định"

# ── Cash Flow ─────────────────────────────────────────────────────────────────
# Lưu chuyển tiền thuần từ HĐKD
COL_CFO   = "Lưu chuyển tiền thuần từ hoạt động kinh doanh"

# Chi mua sắm TSCĐ (sẽ lấy abs() — giá trị âm trong file gốc)
COL_CAPEX = "1. Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác"
