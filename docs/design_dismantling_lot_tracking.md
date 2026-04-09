# Design: Dismantling & Lot Tracking

**Date:** 2026-04-08
**Updated:** 2026-04-09
**Version:** 19.0.2.0.0
**Status:** Implemented
**Supersedes:** design_v2.md sections 9-13 (DOC 3, Inherit Models)

---

## 1. Design Decisions (เหตุผลที่เปลี่ยนจาก v2)

### 1.1 ไม่มี Acquired-level BOM

**v2 (เดิม):** สร้าง BOM ซ้ำอีกชุดผูก acquired แต่ละคัน
**v3 (ใหม่):** ใช้ Spec-level BOM ตัวเดียว ทำ Unbuild ได้เลย

**เหตุผล:**
- Acquired BOM copy มาจาก assessment lines ซึ่ง copy มาจาก spec BOM อีกที = data ซ้ำซ้อน 3 ชั้น
- Unbuild อ้าง Spec BOM ได้ตรงๆ
- ความแตกต่างรายคัน (สภาพจริง, ชิ้นที่หาย) จัดการใน Dismantling Doc แทน

**สิ่งที่ลบ:**
- `action_create_bom` ใน acquired
- `bom_id` field ใน acquired (ที่ผูก acquired-level BOM)
- `itx_acquired_id` field ใน mrp.bom

### 1.2 ไม่มี itx_expected_price / itx_allocated_cost ใน mrp.bom.line

**เหตุผล:**
- BOM = master data → บอกว่ารถรุ่นนี้มีอะไหล่อะไร + สัดส่วนต้นทุน
- expected_price เปลี่ยนทุกคัน → อยู่ใน assessment line เท่านั้น
- allocated_cost คำนวณจาก target_price × cost_weight → ขึ้นกับราคาซื้อแต่ละคัน

**สิ่งที่เหลือใน mrp.bom.line:**
- `itx_cost_weight` — สัดส่วนต้นทุน (master data)
- `itx_total_weight` — compute: ผลรวม cost_weight ทั้ง BOM (realtime)
- `itx_weight_status` — compute: "✓ 100%" / "+2.00%" / "-5.00%"

### 1.3 Lot/Serial Tracking แทน Acquired-level BOM

**เหตุผล:**
- ต้อง trace ว่า part แต่ละชิ้นมาจากซากคันไหน (VIN)
- ต้อง trace ว่าซื้อมาจาก PO ไหน
- เมื่อขาย part หมดคัน → สรุปกำไร/ขาดทุนรายคันได้
- Analytic account ผูกทุก transaction → P&L ต่อคัน

### 1.4 Product Type = consu + is_storable

**Odoo 19 ไม่มี `type='product'` แล้ว**
- storable product = `type='consu'` + `is_storable=True`
- ทุก part (ซากรถ + อะไหล่) ต้อง track on-hand → ต้อง is_storable=True
- ต้อง tracking='lot' → เปิดใช้ lot/serial number

### 1.5 Confirm Stock ยังคงเป็น Manual

> **หมายเหตุ:** Design เดิมเขียนว่าจะลบปุ่ม Confirm Stock แล้วให้ purchased→stocked
> อัตโนมัติเมื่อ Receipt validated แต่ **implementation จริงยังคงปุ่ม manual ไว้ก่อน**
> เพราะยังไม่ได้เขียน automation ตรง Receipt → Acquired state

- `action_confirm_stock` — ยังอยู่ใน acquired model (เปลี่ยน state เป็น 'stocked')
- ปุ่ม "Confirm Stock" — ยังแสดงใน form view เมื่อ state='purchased'
- **TODO:** อนาคตอาจทำ auto เมื่อ Receipt validated ผ่าน stock.picking override

---

## 2. BOM Architecture (ใหม่)

```
Spec-level BOM (master data — 1 ชุดต่อ spec)
├── product: ซากรถ (spec + SALVAGE + OEM + GOOD)
├── bom_line: อะไหล่ 63 ชิ้น
│   ├── product_id (spec + part + OEM + GOOD)
│   ├── product_qty
│   └── itx_cost_weight (% สัดส่วนต้นทุน)
│
├── itx_total_weight (compute: ผลรวม)
└── itx_weight_status (compute: ✓ 100% / ขาด / เกิน)

ใช้สำหรับ:
  1. Generate assessment lines (ทุกครั้ง)
  2. Unbuild (แตก part) → ใช้ BOM เดียวกันได้หลายครั้ง หลายคัน
```

---

## 3. Lot/Serial Tracking

### 3.1 stock.lot (inherit)

| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_vin | Char | VIN ของซากรถที่ part นี้มา |
| itx_acquired_id | Many2one itx.revival.acquired | ผูกกับรถคันไหน |

### 3.2 product.template (ปรับ)

| Field | ค่า | คำอธิบาย |
|---|---|---|
| type | 'consu' | Odoo 19 standard |
| is_storable | True | track on-hand |
| tracking | 'lot' | เปิด lot/serial tracking |

### 3.3 Trace Flow (ตรงกับ implementation จริง)

```
ขาเข้า (ซื้อซาก):
  PO → Receipt → Validate
  → ซากรถ on-hand = 1
  → analytic account ผูก PO line

ขาแตก (Unbuild):
  Dismantling.action_start → สร้าง Unbuild Order จาก Spec BOM
  → ซากรถ on-hand: 1 → 0
  → อะไหล่ on-hand: 0 → qty (OEM&GOOD default)
  (ยังไม่มี lot ณ จุดนี้ — lot สร้างตอน Confirm Done)

Dismantling Confirm Done (สร้าง lot + ปรับสภาพจริง):
  Dismantling.action_done →
  → วนทุก line ที่ is_included=True:
     1. ถ้า actual origin/condition ต่างจาก assessed:
        → lookup/create product ใหม่ตาม actual origin+condition
        → เก็บใน actual_product_id
     2. สร้าง lot สำหรับทุกชิ้น (stamp VIN + acquired_id)
        → lot name = "{VIN}-{part_abbr}"
        → ผูก lot กับ actual_product_id (หรือ product_id ถ้าไม่ต่าง)
  → state → done
  → acquired.state → completed (ถ้าอยู่ dismantling)

ขาออก (ขายอะไหล่):
  SO → Delivery → ระบุ lot ที่ขาย
  → analytic account ผูก SO line
  → trace กลับ: lot → VIN → acquired → PO → ต้นทุน
```

---

## 4. DOC 3: itx.revival.dismantling (Implementation จริง)

### Purpose
เอกสารแตกชิ้นส่วน — confirm สภาพจริงของ part + stamp VIN/lot
ไม่สร้าง BOM ใหม่ — ใช้ Spec BOM ทำ Unbuild ได้เลย

### States
```
draft → in_progress → done
```

### Fields (Header)

| Field | Type | คำอธิบาย |
|---|---|---|
| name | Char (sequence) | DIS/2026/0001 |
| acquired_id | Many2one itx.revival.acquired (required) | รถที่จะแตก |
| assessment_id | related acquired.assessment_id store=True | แบบประเมินต้นทาง |
| spec_id | related store=True | สเปครถ |
| vin | related acquired.vin store=True | VIN |
| dismantling_date | Date | วันที่แตกจริง (set ตอน action_start) |
| technician_id | Many2one res.partner | ช่างที่รื้อ |
| unbuild_id | Many2one mrp.unbuild (readonly) | Unbuild Order (auto สร้างตอน Start) |
| state | Selection | draft/in_progress/done |
| line_ids | One2many itx.revival.dismantling.line | รายการอะไหล่ |
| line_count | Integer (compute) | จำนวน lines |
| note | Text | หมายเหตุ |
| active | Boolean | default=True |

### Buttons / Actions (ตรงกับ code จริง)

| Button | Visible When | Action | คำอธิบาย |
|---|---|---|---|
| Generate Lines | state=draft, line_count=0 | `action_generate_lines` | copy จาก assessment lines (is_found=True) → สร้าง dismantling lines พร้อม assessed+actual columns |
| Start Dismantling | state=draft, line_count>0 | `action_start` | สร้าง Unbuild Order จาก Spec BOM + set dismantling_date + state→in_progress |
| Confirm Done | state=in_progress | `action_done` | วน lines → ปรับ product ถ้า condition ต่าง → สร้าง lot ทุกชิ้น → state→done → acquired→completed |

### Button Box (stat buttons)
| Button | Visible When | คำอธิบาย |
|---|---|---|
| Unbuild Order | unbuild_id exists | เปิด Unbuild Order form |

### action_generate_lines — รายละเอียด
```python
# Source: assessment_id.line_ids ที่ is_found=True และมี product_id
# ลบ lines เดิมทั้งหมดก่อน
# Copy fields:
#   assessed_origin_id  ← assessment_line.part_origin_id
#   assessed_condition_id ← assessment_line.part_condition_id
#   assessed_qty         ← assessment_line.qty_found
#   actual_origin_id     ← copy จาก assessed (ให้ user แก้ทีหลัง)
#   actual_condition_id  ← copy จาก assessed (ให้ user แก้ทีหลัง)
#   actual_qty           ← copy จาก assessed
#   product_id           ← assessment_line.product_id
#   cost_weight          ← assessment_line.cost_weight
#   is_included          ← True
```

### action_start — รายละเอียด
```python
# 1. ต้องมี lines (ไม่งั้น raise UserError)
# 2. หา Spec-level BOM จาก spec_id
# 3. หา product จาก acquired_id.product_id
# 4. สร้าง mrp.unbuild:
#    - product_id = acquired.product_id (ซากรถ)
#    - bom_id = spec-level BOM
#    - product_qty = 1
#    - itx_acquired_id = acquired_id
#    - itx_dismantling_id = self.id
# 5. Set: unbuild_id, dismantling_date=today, state='in_progress'
```

### action_done — รายละเอียด
```python
# 1. ต้องอยู่ state='in_progress'
# 2. วน included_lines (is_included=True):
#    a. ถ้า actual origin/condition ต่างจาก assessed:
#       → _get_or_create_part_product(part_name, actual_origin, actual_condition)
#       → set actual_product_id
#    b. สร้าง stock.lot:
#       → name = "{VIN}-{part_abbr or part_code}"
#       → product_id = actual_product_id or product_id
#       → itx_vin = self.vin
#       → itx_acquired_id = self.acquired_id
#    c. Set lot_id on line
# 3. state → 'done'
# 4. ถ้า acquired.state == 'dismantling' → acquired.state = 'completed'
```

### _get_or_create_part_product — helper
```python
# Lookup product.template ด้วย UK: spec + part_name + origin + condition
# ถ้าไม่เจอ → สร้างใหม่ (consu, is_storable=True, tracking='lot')
# Return product.product (variant)
```

---

## 5. itx.revival.dismantling.line (Implementation จริง)

| Field | Type | Readonly | คำอธิบาย |
|---|---|---|---|
| dismantling_id | Many2one itx.revival.dismantling | required, cascade | หัวเอกสาร |
| sequence | Integer | - | ลำดับ (default=10) |
| part_name_id | Many2one itx.info.vehicle.template.part | required | ชื่ออะไหล่ |
| part_category_id | related part_name_id.category_id | store=True | หมวดหมู่ (auto) |
| assessment_line_id | Many2one itx.revival.assessment.line | readonly | link กลับ assessment line |
| **assessed_origin_id** | Many2one itx.info.vehicle.part.origin | readonly | origin จาก assessment |
| **assessed_condition_id** | Many2one itx.info.vehicle.part.condition | readonly | condition จาก assessment |
| **assessed_qty** | Integer | readonly | จำนวนจาก assessment |
| **actual_origin_id** | Many2one itx.info.vehicle.part.origin | editable | origin จริง (user แก้ได้) |
| **actual_condition_id** | Many2one itx.info.vehicle.part.condition | editable | condition จริง (user แก้ได้) |
| **actual_qty** | Integer | editable | จำนวนจริง (default=1) |
| product_id | Many2one product.product | readonly | product จาก assessment (OEM&GOOD default) |
| actual_product_id | Many2one product.product | readonly | product จริง (set ตอน action_done ถ้า condition ต่าง) |
| lot_id | Many2one stock.lot | readonly | lot ที่สร้างตอน action_done (stamp VIN) |
| cost_weight | Float(5,2) | - | % สัดส่วนต้นทุน |
| is_included | Boolean | editable | รวมใน Dismantling (default: True) |
| note | Char | editable | หมายเหตุ |

### View: list editable="bottom"
- assessed columns = readonly (ดูเปรียบเทียบ)
- actual columns = editable (user กรอกสภาพจริง)
- product_id, actual_product_id, lot_id, cost_weight = optional="hide" (ซ่อนได้)

---

## 6. Acquired Vehicle (Implementation จริง)

### สิ่งที่ลบ (จาก v2)
- `action_create_bom` — ไม่ต้องสร้าง Acquired-level BOM
- `bom_id` field (ที่ผูก acquired-level BOM)

### สิ่งที่ยังคงอยู่ (ต่างจาก design เดิม)
- `action_confirm_stock` — **ยังอยู่** (manual เปลี่ยน purchased→stocked)
- ปุ่ม "Confirm Stock" — **ยังแสดง** เมื่อ state='purchased'

### สิ่งที่เพิ่ม
- `dismantling_id` — Many2one ผูก DOC 3
- `action_create_dismantling` — สร้าง Dismantling Order + เปลี่ยน state→dismantling

### States
```
draft → purchased → stocked → dismantling → completed
```

### Buttons (ตรงกับ view จริง)

| Button | Visible When | คำอธิบาย |
|---|---|---|
| Create PO | state=draft, ยังไม่มี PO | สร้าง Purchase Order |
| Confirm Stock | state=purchased | manual เปลี่ยน state→stocked |
| Create Dismantling | state=stocked, ยังไม่มี dismantling, decision=dismantle | สร้าง DOC 3 + state→dismantling |
| Complete | state=stocked, decision=sell_whole | ปิด cycle สำหรับกรณีขายทั้งคัน |

> **หมายเหตุ:** กรณี decision='dismantle' การเปลี่ยน dismantling→completed
> ทำอัตโนมัติจาก `dismantling.action_done` (ไม่ต้องกดปุ่มใน Acquired)

### Button Box (stat buttons)

| Button | Visible When | คำอธิบาย |
|---|---|---|
| Purchase Order | purchase_order_id exists | เปิด PO form |

> **TODO:** เพิ่ม stat button สำหรับ Dismantling Order ใน acquired form

---

## 7. Inherit Models (Implementation จริง)

### mrp.bom (inherit)
| Field | Type | คำอธิบาย |
|---|---|---|
| itx_spec_id | Many2one itx.info.vehicle.spec | Spec-level BOM (master) |

~~itx_acquired_id~~ — **ลบแล้ว** (ไม่มี acquired-level BOM)

### mrp.bom.line (inherit)
| Field | Type | คำอธิบาย |
|---|---|---|
| itx_cost_weight | Float | % สัดส่วนต้นทุน |
| itx_total_weight | Float (compute) | ผลรวม cost_weight ทั้ง BOM |
| itx_weight_status | Char (compute) | "✓ 100%" / ขาด / เกิน |

~~itx_expected_price~~ — **ลบแล้ว** (ไม่ใช่ master data)
~~itx_allocated_cost~~ — **ลบแล้ว** (คำนวณใน assessment line แทน)

### stock.lot (inherit) — **ไฟล์ใหม่: models/stock_lot.py**
| Field | Type | คำอธิบาย |
|---|---|---|
| itx_vin | Char (index) | VIN ของซากรถต้นทาง |
| itx_acquired_id | Many2one itx.revival.acquired (index) | ผูกกับรถคันไหน |

### mrp.unbuild (inherit)
| Field | Type | คำอธิบาย |
|---|---|---|
| itx_acquired_id | Many2one itx.revival.acquired (index) | ผูกกับรถคันไหน |
| itx_dismantling_id | Many2one itx.revival.dismantling (index) | ผูกกับ Dismantling |

---

## 8. P&L Tracking (กำไร/ขาดทุนรายคัน)

```
1 Acquired Vehicle = 1 Analytic Account

ต้นทุน (Debit):
  ├── PO line (ราคาซื้อซาก)
  ├── Transport cost
  ├── Dismantling cost
  └── Other cost

รายได้ (Credit):
  └── SO lines ที่ขาย part (trace ผ่าน lot → VIN → acquired)

สรุป:
  Actual Revenue = Σ SO lines ของ lots ที่ผูก acquired นี้
  Actual Profit  = Actual Revenue - Total Cost
  Actual ROI     = Actual Profit / Total Cost × 100
  Sold %         = จำนวน lot ที่ขาย / ทั้งหมด × 100
```

> **สถานะ:** _compute_actual_values ใน acquired ยังเป็น TODO — ค่า actual_revenue/profit/roi/sold% = 0 ทั้งหมด
> รอ implement เมื่อมี sale.order.line ผูก lot

---

## 9. Security & Access (Implementation จริง)

### ir.model.access.csv

| Model | User (stock_user) | Manager (stock_manager) |
|---|---|---|
| itx.revival.assessment | Read | Full |
| itx.revival.assessment.line | Read | Full |
| itx.revival.acquired | Read | Full |
| itx.revival.acquired.image | Read | Full |
| itx.revival.dismantling | Read | Full |
| itx.revival.dismantling.line | Read | Full |

---

## 10. Sequences

| Code | Prefix | Padding | ตัวอย่าง |
|---|---|---|---|
| itx.revival.assessment | ASM/%(year)s/ | 4 | ASM/2026/0001 |
| itx.revival.acquired | ACQ/%(year)s/ | 4 | ACQ/2026/0001 |
| itx.revival.dismantling | DIS/%(year)s/ | 4 | DIS/2026/0001 |

---

## 11. Menu Structure

```
Revival Vehicle (root, seq=45)
├── Operations (seq=10)
│   ├── Assessments (seq=10) → itx_revival_assessment_action
│   ├── Acquired Vehicles (seq=20) → itx_revival_acquired_action
│   └── Dismantling Orders (seq=30) → itx_revival_dismantling_action
└── Reports (seq=50) — ว่าง (TODO)
```

---

## 12. __manifest__.py — Dependencies & Data Files

```python
depends = ['itx_info_vehicle', 'mrp', 'purchase', 'account', 'stock']

data = [
    'security/ir.model.access.csv',
    'data/ir_sequence_data.xml',
    'views/itx_revival_assessment_views.xml',
    'views/itx_revival_acquired_views.xml',
    'views/itx_revival_dismantling_views.xml',
    'views/mrp_bom_views.xml',
    'views/menuitems.xml',
]
```

---

## 13. Known TODOs / ยังไม่ implement

1. **_compute_actual_values** — actual revenue/profit/roi/sold% ยังเป็น 0 (รอผูก sale.order.line)
2. **Auto purchased→stocked** — ยังเป็น manual (ปุ่ม Confirm Stock), อาจทำ auto ผ่าน stock.picking override
3. **Dismantling stat button ใน Acquired form** — ยังไม่มี (มีแค่ field dismantling_id แสดงเมื่อมีค่า)
4. **PDF Checklist (Assessment)** — action_print_checklist ยัง raise UserError "ยังไม่พร้อมใช้งาน"
5. **Reports menu** — ว่างเปล่า
6. **Unbuild validation** — action_start สร้าง Unbuild แต่ยังไม่ได้ validate (ต้องไปกด validate ใน MRP manually)
7. **Stock move adjustment** — เมื่อ actual condition ต่างจาก assessed, สร้าง lot ใหม่แต่ยังไม่ได้ทำ stock move ย้าย qty จาก product เดิมไป product ใหม่
