# Pricing Flow: Assessment → Dismantling → Product → e-Commerce

> Version: 1.0 | Date: 2026-04-24

---

## 1. Overview

ราคาขายอะไหล่ถูกกำหนดเป็นขั้นตอน ผ่าน 3 จุด ก่อนถึงมือลูกค้า:

```
Assessment (H/O ประเมิน)
    ↓  expected_price
Dismantling (คนรู้จัก part กำหนดราคาสุดท้าย)
    ↓  sale_price
Product (Odoo standard)
    ↓  lst_price
e-Commerce / SO Line (ลูกค้าเห็นราคานี้)
```

---

## 2. Price Fields ในแต่ละ Model

### 2.1 Assessment Line (`itx.revival.assessment.line`)

| Field | Type | ใครกรอก | ความหมาย |
|---|---|---|---|
| `expected_price` | Float | H/O | ราคาที่คาดว่าขายได้ (ประเมินจากตลาด) |
| `cost_weight` | Float (%) | Auto/H/O | สัดส่วนต้นทุนของ part ต่อรถทั้งคัน |
| `allocated_cost` | Float (computed) | Auto | = target_price × cost_weight / total_weight |

### 2.2 Dismantling Line (`itx.revival.dismantling.line`)

| Field | Type | ใครกรอก | ความหมาย |
|---|---|---|---|
| `assessed_price` | Float (readonly) | Auto | คัดลอกจาก Assessment `expected_price` เพื่อเปรียบเทียบ |
| `sale_price` | Float (editable) | คนรู้จัก part | **ราคาขายจริง** — จุดสุดท้ายก่อนไปขาย |
| `cost_weight` | Float (%) | Auto | สัดส่วนต้นทุน (มาจาก Assessment) |
| `allocated_cost` | Float (computed) | Auto | = purchase_price × cost_weight / total_weight |

### 2.3 Product (`product.product` / `product.template`)

| Field | Level | ความหมาย | ใช้ตรงไหน |
|---|---|---|---|
| `lst_price` | variant (computed) | = list_price + price_extra | e-Commerce แสดงราคานี้ |
| `list_price` | template | ราคาขายพื้นฐาน | SO line default price |
| `price_extra` | variant attribute | ส่วนต่างราคาต่อ attribute value | OEM vs AFT vs USED |
| `standard_price` | variant (per company) | ต้นทุน | Stock valuation, COGS |

---

## 3. Odoo Standard Pricing Mechanism

### 3.1 ราคาขาย (Sales Price)

```
product.template.list_price     = ราคาพื้นฐาน (shared ทุก variant)
+ product.template.attribute.value.price_extra  (per attribute, per template)
= product.product.lst_price     = ราคาจริงที่ลูกค้าเห็น
```

**เมื่อเขียน `product.product.lst_price`** → Odoo inverse (`_set_product_lst_price`) จะ:
1. คำนวณ `value = lst_price - price_extra`
2. เขียนกลับ `product.template.list_price = value`

ผลลัพธ์: e-Commerce แสดงราคาถูกต้องต่อ variant

### 3.2 ต้นทุน (Cost / Standard Price)

```
product.product.standard_price  = ต้นทุนต่อ variant (company_dependent)
```

- ใช้คำนวณ **stock valuation** (มูลค่าสต็อก)
- ใช้คำนวณ **COGS** (ต้นทุนขาย) ตอน deliver สินค้า
- Odoo stock_account module สร้าง journal entry อัตโนมัติ

### 3.3 Pricelist (ถ้าใช้)

Odoo pricelist สามารถ override ราคาได้อีกชั้น:
- ราคาต่อ customer group
- ราคาต่อ quantity
- ราคาต่อ period

**ยังไม่ได้ implement** — ใช้ `lst_price` ตรงๆ ก่อน

---

## 4. Implementation: action_done()

เมื่อกด **Confirm Done** ใน Dismantling:

```python
# === Update product pricing (Odoo standard for e-commerce) ===
for line in included_lines:
    product = line.actual_product_id or line.product_id

    # lst_price → Odoo inverse จะ set list_price + price_extra ให้ถูกต้อง
    if line.sale_price:
        product.lst_price = line.sale_price

    # standard_price = allocated cost (per variant, per company)
    if line.allocated_cost:
        product.standard_price = line.allocated_cost
```

### ทำไมต้อง action_done() ไม่ใช่ action_start()?

| | action_start() | action_done() |
|---|---|---|
| ช่างแก้ sale_price ได้อีก? | ได้ — ยังไม่ final | ไม่ได้ — final แล้ว |
| Part อยู่ใน stock? | ยังไม่ — กำลังรื้อ | ใช่ — เข้า stock แล้ว |
| e-Commerce ควรแสดง? | ยังไม่ — ยังไม่มีของ | ใช่ — พร้อมขาย |

---

## 5. Data Flow Diagram

```
                    Assessment
                    ┌─────────────────────────────┐
                    │ expected_price: 5,000        │
                    │ cost_weight: 8.5%            │
                    │ allocated_cost: 3,400        │
                    └──────────┬──────────────────┘
                               │ Generate Lines
                               ▼
                    Dismantling Line
                    ┌─────────────────────────────┐
                    │ assessed_price: 5,000  (r/o) │
                    │ sale_price: 4,500  (editable)│  ← คนรู้จัก part กำหนด
                    │ cost_weight: 8.5%            │
                    │ allocated_cost: 3,400        │
                    └──────────┬──────────────────┘
                               │ action_done()
                               ▼
                    product.product
                    ┌─────────────────────────────┐
                    │ lst_price: 4,500             │  → e-Commerce
                    │ standard_price: 3,400        │  → Stock Valuation / COGS
                    └──────────┬──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
               e-Commerce             SO Line
            (ลูกค้าเห็น 4,500)    (price_unit: 4,500)
```

---

## 6. Edge Cases

### 6.1 รถหลายคัน Spec เดียวกัน → product เดียวกัน

เช่น Civic FC คัน A และ B ต่างก็มี "ฝากระโปรง / OEM / ดี" = `product.product` ตัวเดียวกัน

- `lst_price` จะถูก overwrite ด้วยคันที่ dismantling ทีหลัง
- สิ่งนี้ **ยอมรับได้** เพราะราคาสะท้อนตลาดปัจจุบัน
- ถ้าต้องการราคาต่อ lot/VIN → ใช้ pricelist หรือแก้ราคาบน SO line ตรง

### 6.2 actual ≠ assessed (origin/condition เปลี่ยน)

ถ้าช่างพบว่า part เป็น AFT แทน OEM → ระบบสร้าง variant ใหม่ให้ → `lst_price` ไปอยู่ถูก variant

### 6.3 sale_price = 0

ถ้าไม่ได้กำหนดราคา → ไม่ update `lst_price` (ป้องกัน overwrite ราคาเก่า)

### 6.4 Margin Analysis

```
Margin per part = sale_price - allocated_cost
                = 4,500 - 3,400
                = 1,100 (กำไรต่อชิ้น)

Margin % = 1,100 / 4,500 = 24.4%
```

สามารถ compute ได้ใน dismantling line ในอนาคต (ยังไม่ได้ implement)

---

## 7. Future Considerations

| หัวข้อ | สถานะ | หมายเหตุ |
|---|---|---|
| Pricelist per customer group | ยังไม่ทำ | ใช้ lst_price ตรงๆ ก่อน |
| Margin field บน dismantling line | ยังไม่ทำ | computed: sale_price - allocated_cost |
| Price history per product | ยังไม่ทำ | ใช้ chatter log หรือ price history ของ Odoo |
| Analytic account integration | ยังไม่ทำ | ดู design_analytic_account_per_vehicle.md |
