# Design: Analytic Account per Vehicle

**Module:** `itx_revival_vehicle`
**Date:** 2026-04-24
**Author:** Chainaris Padungkul + Claude AI
**Status:** Implemented v1.0
**Version:** 2.0

---

## 1. วัตถุประสงค์

ผูก **ทุกกิจกรรมด้านการเงินและบัญชี** เข้า Analytic Account ของรถแต่ละคัน
เพื่อให้สามารถ:

1. ดู **P&L (กำไร/ขาดทุน) ต่อรถแต่ละคัน** ได้ทันที
2. เปรียบเทียบ **Plan vs Actual** — ราคาคาดการณ์ vs ขายจริง
3. ติดตาม **% ขายแล้ว / คงเหลือ** ต่อรถแต่ละคัน
4. ใช้ **Analytic Report มาตรฐานของ Odoo** ได้โดยไม่ต้องเขียน report เอง

---

## 2. VIN = สายสะดือเชื่อมทุกอย่าง

### 2.1 Design Decision: VIN เป็น key เดียวใช้ได้ทุกที่

VIN (Vehicle Identification Number) ทำหน้าที่เป็น **universal key** ของรถทุกคัน:

```
VIN: MHFAA3EM5F0123456
 │
 ├── stock.lot.name = VIN          → ทุก part ที่แตกจากรถคันนี้ใช้ lot เดียวกัน
 │     └── lot.itx_acquired_id    → trace กลับรถคันไหน
 │     └── lot.itx_vin            → VIN ซ้ำอีกชั้น (searchable)
 │
 ├── analytic account name = VIN   → ดู P&L per vehicle
 │     format: "ACQ/2026/0001 | MHFAA3EM5F0123456 | Civic FD 1.8S"
 │              ├── ACQ number     → อ่านง่าย ใช้อ้างอิงในทีม
 │              ├── VIN            → trace ข้ามระบบได้ทันที
 │              └── Spec           → รู้ทันทีว่ารถอะไร
 │
 └── acquired.vin = VIN            → master record ของรถคันนี้
```

**ข้อดี:**
- ดู VIN ตรงไหนก็ได้ในระบบ → trace กลับ lot, acquired, analytic ได้หมด
- ไม่ต้องจำหลาย key — VIN ตัวเดียวพอ
- VIN unique ทั่วโลก — ไม่มีทางซ้ำ

**Timeline ของ VIN ในระบบ:**
```
Assessment (draft)     → vehicle_vin: optional (อาจยังไม่รู้)
Assessment (dismantle) → vehicle_vin: อาจมีหรือไม่มี
  │
  ▼ action_create_acquired()
Acquired (create)      → vin: required=True ← ต้องมี VIN ณ จุดนี้
                          analytic สร้างพร้อมกัน ← VIN มีแน่ ใช้ตั้งชื่อ analytic ได้
```

### 2.2 Analytic Account Naming Format

```
"{ACQ_number} | {VIN} | {Spec_name}"

ตัวอย่าง:
"ACQ/2026/0001 | MHFAA3EM5F0123456 | Civic FD 1.8S"
"ACQ/2026/0002 | MHFAC3GMPK234567 | Vigo 2.5E 4WD"
```

### 2.3 Code Change (เล็กน้อย)

```python
# _create_analytic_account() — แก้ display_name format
display_name = f"{self.name} | {self.vin}"
if self.spec_id:
    display_name += f" | {self.spec_id.full_name}"
```

### 2.4 หลักการ: 1 คัน = 1 Analytic Account

```
Analytic Account: "ACQ/2026/0001 | MHFAA3EM5F0123456 | Civic FD 1.8S"
Plan: "Revival Vehicle"
──────────────────────────────────────────────────────────
  DEBIT (ต้นทุน)                    │  CREDIT (รายได้)
  ───────────────────────────────── │ ─────────────────────────
  ซื้อซาก (PO → Vendor Bill)   120,000 │  ขายกันชนหน้า (SO → Inv)  8,500
  ค่าขนส่ง (Vendor Bill)         5,000 │  ขายไฟหน้าซ้าย            4,200
  ค่ารื้อถอน (Vendor Bill)       8,000 │  ขายเครื่องยนต์           45,000
  ค่าอื่นๆ (Misc JE)            2,000 │  ...
  ───────────────────────────────── │ ─────────────────────────
  รวมต้นทุน                    135,000 │  รวมรายได้                57,700
                                       │
  ➜ P&L ปัจจุบัน = 57,700 - 135,000 = -77,300 (ขาดทุนอยู่)
  ➜ ขายแล้ว 12/54 ชิ้น (22%)
  ➜ Plan: expected revenue 180,000 → expected profit 45,000
  ➜ เมื่อขายครบ: คาดว่ากำไร +45,000 (ROI 33%)
```

---

## 3. Odoo Analytic — กลไกที่ต้องเข้าใจ

### 3.1 analytic_distribution (Odoo 17+)

Odoo 17+ ใช้ `analytic_distribution` แบบ JSON dict แทน Many2one เดิม:

```python
# format: {str(analytic_account_id): percentage}
analytic_distribution = {"42": 100}   # 100% ไป account 42
analytic_distribution = {"42": 60, "43": 40}  # แบ่ง 2 account
```

### 3.2 Analytic ไหลอย่างไรใน Odoo standard

```
PO Line (analytic_distribution)
  └── Vendor Bill Line → inherit จาก PO Line (auto)
      └── Analytic Line สร้างตอน post bill (auto)

SO Line (analytic_distribution)
  └── Customer Invoice Line → inherit จาก SO Line (auto)
      └── Analytic Line สร้างตอน post invoice (auto)
      └── COGS Line → inherit จาก invoice line (auto by stock_account)

Stock Move → Journal Entry (stock_account)
  └── account.move.line → ไม่มี analytic โดย default
      → ต้อง stamp เอง ถ้าต้องการ
```

**สรุป:** ถ้า stamp analytic ที่ **PO Line** และ **SO Line** ให้ถูก → Bill, Invoice, COGS จะ inherit ไปเองอัตโนมัติ ไม่ต้องทำอะไรเพิ่ม

### 3.3 จุดที่ Odoo ไม่ทำให้

| จุด | ทำไมไม่ auto |
|-----|-------------|
| ค่าใช้จ่ายเพิ่ม (transport/dismantling/other) | เป็นแค่ Float field — ไม่มี Journal Entry |
| Stock Move → JE | stock.move ไม่มี `analytic_distribution` field |
| SO ขายอะไหล่ | Odoo ไม่รู้ว่า product นี้มาจากรถคันไหน |

---

## 4. สถานะปัจจุบัน (As-Is)

### 4.1 สิ่งที่ทำแล้ว

| # | จุด | Status | หมายเหตุ |
|---|-----|--------|---------|
| 1 | สร้าง Analytic Account ตอน create Acquired | ✅ Done | `_create_analytic_account()` |
| 2 | Analytic Plan "Revival Vehicle" สร้าง auto | ✅ Done | search or create |
| 3 | PO Line (ซื้อซาก) stamp analytic | ✅ Done | `action_create_po()` line 494-496 |
| 4 | SO Line (ขายยกคัน Path A) stamp analytic | ✅ Done | `action_create_so_dropship()` line 559-561 |

### 4.2 สิ่งที่ยังไม่ทำ

| # | จุด | ปัญหา | ผลกระทบ |
|---|-----|-------|---------|
| 5 | ค่าขนส่ง (transport_cost) | แค่ Float field ไม่มี JE | ❌ ต้นทุนไม่เข้า analytic |
| 6 | ค่ารื้อถอน (dismantling_cost) | เหมือนกัน | ❌ |
| 7 | ค่าอื่นๆ (other_cost) | เหมือนกัน | ❌ |
| 8 | Stock Move (dismantling in/out) | stock.move ไม่มี analytic_distribution | ❌ Stock valuation ไม่ผูก analytic |
| 9 | SO Line (ขายอะไหล่แยกชิ้น) | ไม่รู้ว่า part มาจากรถคันไหน | ❌ **รายได้ไม่เข้า analytic** |
| 10 | `_compute_actual_values()` | return 0 ทั้งหมด (TODO) | ❌ actual revenue/profit/roi ไม่ทำงาน |

---

## 5. To-Be Design: ผูก Analytic ครบทุกจุด

### 5.1 ภาพรวม Flow + จุดที่ต้อง stamp

```
Assessment
  │ action_decide_dismantle
  ▼
Acquired (create → auto analytic account)
  │
  ├── [COST 1] action_create_po()
  │     └── PO Line → analytic ✅ (มีแล้ว)
  │         └── Vendor Bill → inherit auto ✅
  │
  ├── [COST 2] action_create_expense_bill()          ← 🔧 NEW
  │     └── Vendor Bill: ค่าขนส่ง + ค่ารื้อ + อื่นๆ
  │         └── Bill Lines → analytic stamp 🔧
  │
  ├── action_confirm_stock() → releasing → stocked
  │
  ├── action_create_dismantling()
  │     └── Dismantling
  │           ├── action_start() → Unbuild Order
  │           └── action_done()
  │                 ├── Consume Move (ซากรถ out)
  │                 │     └── JE → analytic stamp 🔧
  │                 └── Produce Moves (อะไหล่ in)
  │                       └── JE → analytic stamp 🔧
  │
  └── [REVENUE] Sale Order (ขายอะไหล่แยกชิ้น)
        └── SO Line → analytic stamp 🔧               ← 🔧 CRITICAL
            └── Customer Invoice → inherit auto ✅
            └── COGS → inherit auto ✅

  ═══════════════════════════════════════════════
  Analytic Report: ดู P&L per vehicle ได้ทันที
  _compute_actual_values(): query จาก analytic lines
```

### 5.2 Implementation Plan — 4 Tasks

---

#### Task 1: ค่าใช้จ่ายเพิ่มเติม → Vendor Bill

**ปัญหา:** `transport_cost`, `dismantling_cost`, `other_cost` เป็นแค่ Float field ไม่มี JE

**แนวทาง:** สร้าง Vendor Bill (account.move, type=in_invoice) สำหรับค่าใช้จ่ายเพิ่ม stamp analytic

```python
# itx_revival_acquired.py — method ใหม่
def action_create_expense_bill(self):
    """สร้าง Vendor Bill สำหรับค่าใช้จ่ายเพิ่มเติม (transport/dismantling/other)"""
    self.ensure_one()
    lines = []
    expense_account = self.company_id.account_expense_id  # หรือ account เฉพาะ

    if self.transport_cost:
        lines.append({
            'name': f'{self.name} - ค่าขนส่ง',
            'quantity': 1,
            'price_unit': self.transport_cost,
            'analytic_distribution': {str(self.analytic_account_id.id): 100},
        })
    if self.dismantling_cost:
        lines.append({
            'name': f'{self.name} - ค่ารื้อถอน',
            'quantity': 1,
            'price_unit': self.dismantling_cost,
            'analytic_distribution': {str(self.analytic_account_id.id): 100},
        })
    if self.other_cost:
        lines.append({
            'name': f'{self.name} - ค่าใช้จ่ายอื่น',
            'quantity': 1,
            'price_unit': self.other_cost,
            'analytic_distribution': {str(self.analytic_account_id.id): 100},
        })

    if not lines:
        raise UserError('ไม่มีค่าใช้จ่ายเพิ่มเติม')

    bill = self.env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': self.vendor_id.id or False,
        'invoice_origin': self.name,
        'invoice_line_ids': [(0, 0, vals) for vals in lines],
    })
    # link bill กลับ acquired
    self.expense_bill_id = bill.id
```

**Field เพิ่ม:**

```python
expense_bill_id = fields.Many2one('account.move', string='Expense Bill', readonly=True)
```

**ทางเลือก:** ให้ user สร้าง Bill เอง (manual) แล้วเราแค่แนะนำให้ผูก analytic → ง่ายกว่าแต่ user อาจลืม

**แนะนำ:** ใช้ปุ่ม auto สร้าง Bill (semi-auto) → user ตรวจ → post เอง

---

#### Task 2: Stock Moves (Dismantling) → stamp analytic บน JE

**ปัญหา:** `stock.move` ไม่มี `analytic_distribution` field → JE ที่สร้างจาก stock valuation ไม่มี analytic

**แนวทาง:** stamp analytic บน account.move.line หลังจาก stock move done

```python
# itx_revival_dismantling.py — เพิ่มใน action_done() หลัง moves done
def _stamp_analytic_on_stock_journal_entries(self, moves):
    """Stamp analytic distribution on JE created by stock moves"""
    analytic_id = self.acquired_id.analytic_account_id
    if not analytic_id:
        return
    distribution = {str(analytic_id.id): 100}
    for move in moves:
        if move.account_move_id:
            for aml in move.account_move_id.line_ids:
                if not aml.analytic_distribution:
                    aml.analytic_distribution = distribution
```

**ข้อควรระวัง:**
- ต้องทำ **หลัง** `_action_done()` เพราะ JE สร้างตอน done
- ถ้า product ใช้ `standard` costing → JE อาจไม่สร้าง (ขึ้นกับ config)
- ถ้า product ใช้ `fifo`/`average` → JE สร้างแน่
- **ถ้าไม่ได้ใช้ Automated Valuation (perpetual)** → ไม่มี JE จาก stock move เลย → Task นี้ไม่จำเป็น

**คำถามที่ต้อง confirm:**
> พี่ชัย DP ใช้ Automated Valuation (perpetual) หรือ Manual Valuation (periodic)?
> ถ้า manual → skip Task นี้ได้ เพราะ stock move ไม่สร้าง JE

---

#### Task 3: SO ขายอะไหล่ → auto stamp analytic (CRITICAL)

**ปัญหา:** เมื่อ user สร้าง SO ขายอะไหล่ → SO line ไม่รู้ว่า part นี้มาจากรถคันไหน

**กลไก traceability ที่มีอยู่แล้ว:**

```
product.product (variant)
  └── stock.lot (VIN as lot name)
        ├── itx_acquired_id → itx.revival.acquired
        │                        └── analytic_account_id ✅
        └── itx_vin ✅
```

**แนวทาง A: stamp ตอน SO confirm (override action_confirm)**

```python
# sale_order.py (inherit) — ใหม่
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        self._stamp_revival_analytic()
        return res

    def _stamp_revival_analytic(self):
        """Auto-stamp analytic from lot → acquired → analytic account"""
        for order in self:
            for line in order.order_line:
                if not line.product_id or line.analytic_distribution:
                    continue  # ข้ามถ้ามี analytic อยู่แล้ว

                # หา lot ที่ reserve ให้ SO line นี้
                lot = self._find_lot_for_so_line(line)
                if not lot or not lot.itx_acquired_id:
                    continue

                analytic = lot.itx_acquired_id.analytic_account_id
                if analytic:
                    line.analytic_distribution = {str(analytic.id): 100}
```

**แนวทาง B: stamp ตอน delivery (stock.picking validate)**

ข้อดี: ตอน delivery → lot/serial เลือกแน่นอนแล้ว → trace ได้ 100%

```python
# stock_picking.py (inherit) — ใหม่
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        self._stamp_revival_analytic_on_so()
        return res

    def _stamp_revival_analytic_on_so(self):
        """After delivery, stamp analytic on SO line from lot → acquired"""
        for picking in self:
            if picking.picking_type_code != 'outgoing':
                continue
            for ml in picking.move_line_ids:
                lot = ml.lot_id
                if not lot or not lot.itx_acquired_id:
                    continue
                analytic = lot.itx_acquired_id.analytic_account_id
                if not analytic:
                    continue

                # Find SO line linked to this move
                so_line = ml.move_id.sale_line_id
                if so_line and not so_line.analytic_distribution:
                    so_line.analytic_distribution = {str(analytic.id): 100}
```

**แนะนำ: แนวทาง B (stamp ตอน delivery)**

เหตุผล:
1. ตอน delivery lot/serial ถูกเลือกแน่นอนแล้ว (ตอน SO confirm ยังไม่รู้ lot)
2. ถ้า user เลือก lot ผิดแล้วแก้ → analytic จะ stamp ตาม lot ล่าสุด
3. Invoice สร้างหลัง delivery → inherit analytic จาก SO line ได้ทัน

**ข้อจำกัด:**
- ใช้ได้เฉพาะ product ที่ track by lot/serial
- ถ้า product ไม่ track → ไม่รู้ว่ามาจากรถคันไหน → ไม่ stamp (acceptable)

---

#### Task 4: `_compute_actual_values()` — query จาก analytic lines

**ปัญหา:** ปัจจุบัน return 0 ทั้งหมด

**แนวทาง:** เมื่อ Task 1-3 เสร็จ → ทุก transaction ผูก analytic → query ได้

```python
# itx_revival_acquired.py
@api.depends('analytic_account_id')
def _compute_actual_values(self):
    for rec in self:
        if not rec.analytic_account_id:
            rec.actual_revenue = 0
            rec.actual_profit = 0
            rec.actual_roi = 0
            rec.sold_percentage = 0
            continue

        # Query analytic lines for this account
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', rec.analytic_account_id.id),
        ])

        # Revenue = positive amounts (credit side = ขาย)
        revenue = sum(l.amount for l in analytic_lines if l.amount > 0)
        # Cost = negative amounts (debit side = ซื้อ/ค่าใช้จ่าย)
        cost = abs(sum(l.amount for l in analytic_lines if l.amount < 0))

        rec.actual_revenue = revenue
        rec.actual_profit = revenue - cost
        rec.actual_roi = (rec.actual_profit / cost * 100) if cost else 0

        # Sold % — count SO lines with this analytic that are delivered
        # (ต้อง refine logic ตาม business requirement)
        total_parts = len(rec.assessment_id.line_ids.filtered('is_found'))
        if total_parts:
            sold_lots = self.env['stock.lot'].search_count([
                ('itx_acquired_id', '=', rec.id),
                ('quant_ids.quantity', '<=', 0),  # out of stock = sold
            ])
            rec.sold_percentage = (sold_lots / total_parts) * 100
        else:
            rec.sold_percentage = 0
```

**หมายเหตุ:** depends ควรใช้ trigger อื่น (ไม่ใช่ analytic_account_id ที่ไม่เปลี่ยน)
→ อาจใช้ cron job recompute ทุกวัน หรือ trigger จาก invoice post

---

## 6. Fields ใหม่ที่ต้องเพิ่ม

### itx.revival.acquired

```python
expense_bill_id = fields.Many2one(
    'account.move', string='Expense Bill',
    readonly=True, copy=False,
    help='Vendor Bill สำหรับค่าขนส่ง/ค่ารื้อถอน/อื่นๆ',
)
expense_bill_count = fields.Integer(
    compute='_compute_expense_bill_count',
)
```

### sale.order.line (inherit) — ไม่ต้องเพิ่ม field (ใช้ analytic_distribution ที่มีอยู่)

### stock.picking (inherit) — ไม่ต้องเพิ่ม field (override method เท่านั้น)

---

## 7. สิ่งที่ Odoo ทำให้ Auto (ไม่ต้องเขียนเพิ่ม)

| รายการ | กลไก | เงื่อนไข |
|--------|-------|---------|
| Vendor Bill inherit analytic จาก PO Line | `purchase.account_invoice._related_analytic_distribution()` | PO line ต้องมี analytic |
| Customer Invoice inherit analytic จาก SO Line | `sale.order.line._set_analytic_distribution()` | SO line ต้องมี analytic |
| COGS line inherit analytic จาก Invoice Line | `stock_account.account_move._get_cogs_related_valuation_lines()` | Invoice line ต้องมี analytic |
| Analytic Lines สร้างตอน post JE | `account.move.post()` → auto create analytic.line | JE line ต้องมี analytic_distribution |

**สรุป: ถ้า stamp analytic ที่ PO Line + SO Line + Expense Bill ให้ถูก → ทุกอย่างไหลต่อเอง**

---

## 8. ความซับซ้อนในการ implement

### 8.1 ทำไมไม่ซับซ้อน?

Chain ที่ต้องการมีอยู่แล้วครบ — แค่ stamp analytic_distribution ตามจุด:

```python
# Core logic ทั้งหมด จริงๆ แค่นี้:
analytic = lot.itx_acquired_id.analytic_account_id
line.analytic_distribution = {str(analytic.id): 100}
# จบ — Odoo propagate ต่อให้เอง (Bill, Invoice, COGS)
```

### 8.2 ประมาณการโค้ดที่ต้องเขียน

| Task | บรรทัดโค้ดโดยประมาณ | ความซับซ้อน |
|------|---------------------|-----------|
| Task 1: Expense Bill | ~40 lines | ต่ำ (สร้าง account.move + stamp) |
| Task 2: Stock Move JE | ~15 lines | ต่ำ (stamp หลัง _action_done) |
| Task 3: SO → analytic | ~25 lines | ต่ำ (override button_validate) |
| Task 4: _compute_actual | ~30 lines | กลาง (query analytic lines) |
| Analytic naming (VIN) | ~5 lines | ต่ำ (แก้ display_name format) |
| **รวม** | **~115 lines** | **ต่ำ-กลาง** |

### 8.3 Priority & Dependencies

```
Task 3 (SO → analytic)        ← CRITICAL — ไม่มี revenue side = ไม่มี P&L
  │
  ├── Task 4 (_compute_actual) ← ต้องรอ Task 3 (ไม่งั้นไม่มี data)
  │
Task 1 (Expense Bill)          ← IMPORTANT — ค่าใช้จ่ายเพิ่มเป็นต้นทุนจริง
  │
Task 2 (Stock Move JE)         ← OPTIONAL — ขึ้นกับ valuation method
```

**ลำดับ implement แนะนำ:**

1. **Task 3** → SO ขายอะไหล่ auto stamp analytic (revenue side)
2. **Task 1** → ค่าใช้จ่ายเพิ่มเป็น Vendor Bill (cost side)
3. **Task 4** → `_compute_actual_values()` query จาก analytic
4. **Task 2** → Stock Move JE stamp analytic (ถ้า perpetual valuation)

### 8.4 Prerequisite: ทดสอบ Dismantling Flow ให้จบก่อน

> **สำคัญ:** ต้องทดสอบ flow Assessment → Acquired → Dismantling → Parts Ready
> ให้ทำงานถูกต้องก่อน แล้วค่อยเพิ่ม analytic ทีหลัง
>
> เหตุผล:
> - Analytic เป็น "ชั้นเสริม" ที่วางทับบน flow หลัก
> - ถ้า flow หลักยังมี bug → แก้ทั้ง flow + analytic พร้อมกันจะยุ่ง
> - เมื่อ flow หลักเสถียร → เพิ่ม analytic ได้ภายใน 1 session

---

## 9. Analytic Report ที่ DP จะได้ใช้

เมื่อ implement ครบ → DP ใช้ Odoo standard reports ได้:

### 9.1 Analytic P&L per Vehicle

```
เมนู: Accounting → Reporting → Analytic → Analytic Items
Filter: Plan = "Revival Vehicle"
Group by: Analytic Account

Account                           │ Debit    │ Credit   │ Balance
──────────────────────────────────│──────────│──────────│──────────
ACQ/2026/0001 - Civic FD 1.8S    │ 135,000  │  57,700  │ -77,300
ACQ/2026/0002 - Vigo 2.5E        │  85,000  │ 120,000  │ +35,000 ✓
ACQ/2026/0003 - Fortuner 2.7V    │ 210,000  │  45,000  │ -165,000
```

### 9.2 Analytic P&L per Vehicle — Detail Drill-down

```
ACQ/2026/0001 - Civic FD 1.8S 2009
──────────────────────────────────────────────────────────
Date        │ Description           │ Debit   │ Credit
────────────│───────────────────────│─────────│────────
2026-03-01  │ PO: ซื้อซาก           │ 120,000 │
2026-03-05  │ Bill: ค่าขนส่ง        │   5,000 │
2026-03-10  │ Bill: ค่ารื้อถอน      │   8,000 │
2026-03-12  │ Bill: ค่าอื่นๆ        │   2,000 │
2026-03-20  │ INV: กันชนหน้า        │         │  8,500
2026-03-25  │ INV: ไฟหน้าซ้าย       │         │  4,200
2026-04-01  │ INV: เครื่องยนต์       │         │ 45,000
            │                       │─────────│────────
            │ Balance               │ 135,000 │ 57,700
            │ P&L                   │         │ -77,300
```

### 9.3 ROI Dashboard (computed fields ใน Acquired)

```
Vehicle          │ Total Cost │ Revenue │ Profit  │ ROI %  │ Sold %
─────────────────│────────────│─────────│─────────│────────│────────
Civic FD 1.8S    │   135,000  │  57,700 │ -77,300 │ -57.3% │  22%
Vigo 2.5E        │    85,000  │ 120,000 │ +35,000 │ +41.2% │  78%
Fortuner 2.7V    │   210,000  │  45,000 │-165,000 │ -78.6% │  15%
```

---

## 10. Open Questions

| # | คำถาม | ผลกระทบ |
|---|-------|---------|
| Q1 | DP ใช้ Automated Valuation (perpetual) หรือ Manual (periodic)? | ถ้า manual → skip Task 2 (stock JE ไม่มี) |
| Q2 | ค่าใช้จ่ายเพิ่ม (transport/dismantling/other) ต้องลง vendor เดียวกับประกัน หรือ vendor แยก? | กำหนด partner_id บน expense bill |
| Q3 | ค่าใช้จ่ายเพิ่มต้องแยก Bill ต่อรายการ หรือรวม Bill เดียว? | UX design ของปุ่ม |
| Q4 | SO ขายอะไหล่ user สร้างเอง (manual) หรือต้องสร้างจากระบบ? | ถ้า manual → ต้อง stamp analytic ตอน delivery (Task 3B) |
| Q5 | `_compute_actual_values()` ต้อง realtime หรือ recompute ทุกวัน (cron) พอ? | Performance vs accuracy |
| Q6 | Expense account สำหรับค่าขนส่ง/ค่ารื้อถอน ใช้ account ไหน? | ต้องตั้ง config หรือ hardcode |

---

## 11. Risks

| # | ความเสี่ยง | โอกาส | ผลกระทบ | การป้องกัน |
|---|-----------|-------|---------|-----------|
| R1 | User สร้าง SO โดยไม่เลือก lot → analytic ไม่ stamp | กลาง | Revenue ไม่เข้า analytic | Warning หรือ enforce lot selection |
| R2 | Product ไม่ track by lot → ไม่สามารถ trace กลับรถคันไหน | ต่ำ | ต้อง track ทุก vehicle part by lot | Vehicle part product ตั้ง tracking='lot' ตั้งแต่สร้าง (มีแล้ว) |
| R3 | User แก้ analytic_distribution บน SO line เอง → ทับค่าที่ stamp | ต่ำ | Analytic ผิด | ใช้ readonly หรือ warning |
| R4 | Performance ลดลงเมื่อ analytic lines เยอะ (1000+ vehicles) | ต่ำ | _compute_actual ช้า | ใช้ SQL query แทน ORM search |
| R5 | Expense Bill สร้างซ้ำ (กดปุ่มหลายครั้ง) | กลาง | ค่าใช้จ่ายซ้ำ | Check expense_bill_id before create |

---

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-24 | Initial design — As-Is/To-Be, 4 Tasks, pseudocode |
| 1.1 | 2026-04-24 | เพิ่ม: VIN as universal key (section 2), analytic naming format, ประมาณการโค้ด, prerequisite note |
| 2.0 | 2026-04-24 | Implemented: Task 0 (naming), Task 1 (expense bill), Task 3 (SO stamp), Task 4 (compute actuals). MRP removed. |

---

*Authors: Chainaris Padungkul + Claude AI*
